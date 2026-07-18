import { starsFor } from "./stars";

describe("starsFor", () => {
  it("dá 3 estrelas a partir de 90%", () => {
    expect(starsFor({ completed: true, score: 90 })).toBe(3);
    expect(starsFor({ completed: true, score: 100 })).toBe(3);
  });

  it("dá 2 estrelas entre 70% e 89%", () => {
    expect(starsFor({ completed: true, score: 70 })).toBe(2);
    expect(starsFor({ completed: true, score: 89 })).toBe(2);
  });

  it("dá 1 estrela a quem passou raspando", () => {
    // 60 é o PASS_THRESHOLD do backend: passou, então nunca fica sem estrela.
    expect(starsFor({ completed: true, score: 60 })).toBe(1);
  });

  it("não dá estrela para lição não concluída, por maior que seja o score", () => {
    // `completed` é o que o backend vira no limiar de aprovação — um score
    // alto sem completed significa que a lição não foi finalizada.
    expect(starsFor({ completed: false, score: 95 })).toBe(0);
  });

  it("tolera lição sem score e entrada ausente", () => {
    expect(starsFor({ completed: true })).toBe(1);
    expect(starsFor(undefined)).toBe(0);
  });
});
