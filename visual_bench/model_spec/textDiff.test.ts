import { describe, expect, it } from "vitest";
import { detokenize, wordDiff } from "./textDiff";

describe("detokenize", () => {
  it("reattaches punctuation and contractions that NLTK split off", () => {
    expect(detokenize("I do n't know , is MSSA bad ? ")).toBe("I don't know, is MSSA bad?");
  });
});

describe("wordDiff", () => {
  it("treats a retokenized copy as unchanged", () => {
    expect(wordDiff("Is MSSA bad?", "Is MSSA bad ? ")).toEqual([{ text: "Is MSSA bad?", op: "same" }]);
  });

  it("shows a typo as the original word removed and the perturbed word added", () => {
    expect(wordDiff("primary differences between MRSA", "primary differences betewen MRSA ")).toEqual([
      { text: "primary differences", op: "same" }, { text: "between", op: "del" }, { text: "betewen", op: "add" },
      { text: "MRSA", op: "same" }]);
  });

  it("shows deleted and repeated words", () => {
    expect(wordDiff("Please help. 2nd degree burn.", "Please help . 2nd burn . ")).toEqual([
      { text: "Please help. 2nd", op: "same" }, { text: "degree", op: "del" }, { text: "burn.", op: "same" }]);
    expect(wordDiff("Please help.", "Please help help . ")).toEqual([
      { text: "Please", op: "same" }, { text: "help", op: "add" }, { text: "help.", op: "same" }]);
  });
});
