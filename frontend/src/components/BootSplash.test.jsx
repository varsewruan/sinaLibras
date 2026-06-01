import { act, render, screen } from "@testing-library/react";

// Capture the subscriber so the test can drive cold-start state.
let coldStartCallback = null;

jest.mock("@/lib/api", () => ({
  onColdStart: (cb) => {
    coldStartCallback = cb;
    cb(false); // emit current (inactive) state on subscribe
    return () => { coldStartCallback = null; };
  },
}));

import { BootSplash } from "./BootSplash";

beforeEach(() => {
  jest.useFakeTimers();
  coldStartCallback = null;
});

afterEach(() => {
  jest.useRealTimers();
});

test("renders nothing while the backend is responsive", () => {
  render(<BootSplash />);
  expect(screen.queryByTestId("boot-splash")).not.toBeInTheDocument();
});

test("renders the splash when cold-start becomes active", () => {
  render(<BootSplash />);
  act(() => coldStartCallback(true));
  expect(screen.getByTestId("boot-splash")).toBeInTheDocument();
  expect(screen.getByTestId("boot-splash-message")).toHaveTextContent(/acordando/i);
});

test("escalates the message as time passes", () => {
  render(<BootSplash />);
  act(() => coldStartCallback(true));
  expect(screen.getByTestId("boot-splash-message")).toHaveTextContent(/acordando/i);

  act(() => jest.advanceTimersByTime(8_000));
  expect(screen.getByTestId("boot-splash-message")).toHaveTextContent(/demorando/i);

  act(() => jest.advanceTimersByTime(15_000));
  expect(screen.getByTestId("boot-splash-message")).toHaveTextContent(/quase l/i);
});
