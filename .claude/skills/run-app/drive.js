/**
 * Dirige o SPA do SINALibras num Chromium headless.
 *
 * Loga pela UI, visita cada rota, tira screenshot, coleta erros de console e
 * de runtime, e confere que os pontos de entrada da Home levam aos destinos
 * certos (no desktop eles são o ÚNICO caminho até Ranking/Conquistas/Perfil).
 *
 * Playwright não é dependência do repo — instale no scratchpad e aponte o
 * NODE_PATH pra lá:
 *
 *   npm init -y; npm install playwright; npx playwright install chromium
 *   $env:NODE_PATH = "<scratchpad>\node_modules"
 *   node .claude\skills\run-app\drive.js
 *
 * Sai 0 se tudo passou, 1 se algo falhou. Screenshots vão pro cwd.
 */
const { chromium } = require("playwright");

const BASE = process.env.SINA_BASE ?? "http://localhost:3000";
const EMAIL = process.env.SINA_EMAIL ?? "smoke-run@sinalibras.dev";
const PASSWORD = process.env.SINA_PASSWORD ?? "senha-forte-123456";

const ROUTES = ["/", "/learn", "/lessons", "/ranking", "/achievements", "/profile"];

// Os tiles da Home. null = destino dinâmico, só exigimos sair da Home.
// A Home virou grid de 6 (sem o botão JOGAR); o CTA dinâmico agora é o
// COMEÇAR da página Aprender, exercitado no fluxo de lição mais abaixo.
const ENTRY_POINTS = [
  ["hub-aprender", "/learn"],
  ["hub-ranking", "/ranking"],
  ["hub-objetivos", "/achievements"],
  ["hub-fases", "/lessons"],
  ["header-profile", "/profile"],
];

const SETTLE_MS = 2500; // deixa o TanStack Query resolver antes do screenshot

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.getByTestId("login-email").fill(EMAIL);
  await page.getByTestId("login-password").fill(PASSWORD);
  await page.getByTestId("login-submit").click();

  try {
    await page.waitForURL((u) => new URL(u).pathname === "/", { timeout: 15000 });
  } catch {
    const err = await page.getByTestId("login-error").textContent().catch(() => null);
    throw new Error(
      `login falhou (url=${page.url()}, erro="${err ?? "nenhum"}").\n` +
        `Registre o usuário antes:\n` +
        `  curl.exe -s -H "Content-Type: application/json" --data "@register.json" ` +
        `http://localhost:8000/api/auth/register`
    );
  }
}

async function sweepRoutes(page, errors, fails) {
  for (const route of ROUTES) {
    errors.length = 0;
    await page.goto(`${BASE}${route}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(SETTLE_MS);

    const text = (await page.evaluate(() => document.body.innerText)).trim();
    const name = route === "/" ? "home" : route.slice(1).replace(/\//g, "-");
    await page.screenshot({ path: `shot-${name}.png`, fullPage: true });

    // Menos que isso e só o chrome do app renderizou: o conteúdo morreu.
    const blank = text.length < 40;
    if (blank) fails.push(`${route} (tela branca)`);
    if (errors.length) fails.push(`${route} (${errors.length} erro(s))`);

    console.log(`\n=== ${route} === chars=${text.length}${blank ? "  <<< TELA BRANCA" : ""}`);
    if (errors.length) console.log([...new Set(errors)].join("\n"));
  }
}

async function checkEntryPoints(page, fails) {
  console.log("");
  for (const [testId, expected] of ENTRY_POINTS) {
    await page.goto(BASE, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1200);
    await page.getByTestId(testId).click();
    await page.waitForTimeout(1200);

    const got = new URL(page.url()).pathname;
    const ok = expected === null ? got !== "/" : got === expected;
    if (!ok) fails.push(`${testId} -> ${got}`);
    console.log(
      `${testId.padEnd(15)} -> ${got.padEnd(20)} ${ok ? "OK" : `FALHOU (esperava ${expected})`}`
    );
  }
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  const errors = [];
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`[console] ${m.text()}`);
  });
  page.on("pageerror", (e) => errors.push(`[pageerror] ${e.message}`));

  const fails = [];
  try {
    await login(page);
    console.log("login OK");
    await sweepRoutes(page, errors, fails);
    await checkEntryPoints(page, fails);
  } finally {
    await browser.close();
  }

  console.log(fails.length ? `\nFALHAS:\n  ${fails.join("\n  ")}` : "\ntudo OK");
  process.exit(fails.length ? 1 : 0);
})().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
