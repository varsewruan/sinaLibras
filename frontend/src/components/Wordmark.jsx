/**
 * O nome do app, centralizado e numa cor só (azul da marca).
 *
 * Já foi bicolor (SINA amarelo + Libras azul); virou cor única em 2026-07-18.
 * O amarelo continua sendo a cor secundária da marca — só não é mais gasto no
 * logotipo, que fica como âncora neutra enquanto o amarelo marca o que dá
 * pra apertar.
 *
 * Renderiza um <h1> por padrão. Onde já existe um h1 na página (ou onde é só
 * chrome, como no topo), passe `as="span"` — dois h1 na mesma tela confundem
 * a navegação por cabeçalhos de leitor de tela.
 */

export const Wordmark = ({ className = "", as: Tag = "h1" }) => (
  <Tag className={`block text-center font-black leading-none tracking-tight text-[#4a97ff] ${className}`}>
    SINALibras
  </Tag>
);
