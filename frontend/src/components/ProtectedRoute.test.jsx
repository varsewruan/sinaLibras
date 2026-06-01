// react-router-dom 7 ships subpath exports that jest 27 (shipped with CRA)
// can't resolve. We don't need the real router for this test — just the
// two pieces ProtectedRoute consumes.
import { render, screen } from "@testing-library/react";

const mockUseAuth = jest.fn();

jest.mock("@/context/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock("react-router-dom", () => ({
  Navigate: ({ to }) => <div data-testid="redirect">redirected to {to}</div>,
  useLocation: () => ({ pathname: "/private" }),
}));

import { ProtectedRoute } from "./ProtectedRoute";

afterEach(() => mockUseAuth.mockReset());

test("shows a loading placeholder while auth is hydrating", () => {
  mockUseAuth.mockReturnValue({ status: "loading" });
  render(
    <ProtectedRoute>
      <div>Secret content</div>
    </ProtectedRoute>
  );
  expect(screen.getByText(/carregando/i)).toBeInTheDocument();
  expect(screen.queryByText(/secret content/i)).not.toBeInTheDocument();
  expect(screen.queryByTestId("redirect")).not.toBeInTheDocument();
});

test("redirects anonymous users to /login", () => {
  mockUseAuth.mockReturnValue({ status: "anonymous" });
  render(
    <ProtectedRoute>
      <div>Secret content</div>
    </ProtectedRoute>
  );
  expect(screen.getByTestId("redirect")).toHaveTextContent("/login");
  expect(screen.queryByText(/secret content/i)).not.toBeInTheDocument();
});

test("renders children for authenticated users", () => {
  mockUseAuth.mockReturnValue({ status: "authenticated" });
  render(
    <ProtectedRoute>
      <div>Secret content</div>
    </ProtectedRoute>
  );
  expect(screen.getByText(/secret content/i)).toBeInTheDocument();
  expect(screen.queryByTestId("redirect")).not.toBeInTheDocument();
});
