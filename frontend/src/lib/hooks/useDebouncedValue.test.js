import { act, renderHook } from "@testing-library/react";

import { useDebouncedValue } from "./useDebouncedValue";

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

test("returns the initial value synchronously", () => {
  const { result } = renderHook(() => useDebouncedValue("a", 250));
  expect(result.current).toBe("a");
});

test("waits for the delay to settle before emitting the new value", () => {
  const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 250), {
    initialProps: { v: "a" },
  });

  rerender({ v: "b" });
  expect(result.current).toBe("a");

  act(() => jest.advanceTimersByTime(249));
  expect(result.current).toBe("a");

  act(() => jest.advanceTimersByTime(1));
  expect(result.current).toBe("b");
});

test("only the latest value wins when changes arrive faster than the delay", () => {
  const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 250), {
    initialProps: { v: "a" },
  });

  rerender({ v: "b" });
  act(() => jest.advanceTimersByTime(100));
  rerender({ v: "c" });
  act(() => jest.advanceTimersByTime(100));
  rerender({ v: "d" });
  expect(result.current).toBe("a");

  act(() => jest.advanceTimersByTime(250));
  expect(result.current).toBe("d");
});
