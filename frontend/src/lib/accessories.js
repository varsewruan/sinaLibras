/**
 * Emoji de cada acessório da loja, por id.
 *
 * O backend (`app/models/shop.py`) é a autoridade sobre ids, rótulos e preços;
 * este mapa existe só para o avatar conseguir desenhar o acessório sem ter que
 * buscar o catálogo inteiro toda vez que renderiza uma listinha de gente (o
 * ranking, por exemplo). **Manter em sync com ACCESSORY_ITEMS.**
 *
 * Id desconhecido → null, e o avatar simplesmente aparece sem chapéu. Um
 * acessório novo no backend some da tela até ser adicionado aqui; nunca quebra.
 */
export const ACCESSORY_EMOJI = {
  "acc-oculos-vermelho": "🕶️",
  "acc-oculos-grau": "👓",
  "acc-bone": "🧢",
  "acc-fones": "🎧",
  "acc-cachecol": "🧣",
  "acc-oculos-esqui": "🥽",
  "acc-laco": "🎀",
  "acc-flores": "🌸",
  "acc-festa": "🥳",
  "acc-cowboy": "🤠",
  "acc-capacete": "⛑️",
  "acc-cartola": "🎩",
  "acc-capelo": "🎓",
  "acc-coracoes": "😍",
  "acc-coroa": "👑",
};

export const accessoryEmoji = (id) => (id ? ACCESSORY_EMOJI[id] ?? null : null);
