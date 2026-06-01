// See ProtectedRoute.test.jsx for why we mock react-router-dom wholesale
// rather than using a MemoryRouter.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mockLogin = jest.fn();
const mockNavigate = jest.fn();
const mockToastError = jest.fn();

jest.mock("@/context/AuthContext", () => ({
  useAuth: () => ({ login: mockLogin }),
}));

jest.mock("react-router-dom", () => ({
  Link: ({ to, children }) => <a href={to}>{children}</a>,
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: null }),
}));

jest.mock("sonner", () => ({
  toast: { error: (...args) => mockToastError(...args), success: jest.fn() },
}));

import Login from "./Login";

beforeEach(() => {
  mockLogin.mockReset();
  mockNavigate.mockReset();
  mockToastError.mockReset();
});

test("submits the form and navigates home on success", async () => {
  mockLogin.mockResolvedValue({ id: "u1", email: "a@b.com" });
  render(<Login />);

  await userEvent.type(screen.getByTestId("login-email"), "a@b.com");
  await userEvent.type(screen.getByTestId("login-password"), "hunter2");
  await userEvent.click(screen.getByTestId("login-submit"));

  expect(mockLogin).toHaveBeenCalledWith({ email: "a@b.com", password: "hunter2" });
  expect(mockNavigate).toHaveBeenCalledWith("/", { replace: true });
  expect(mockToastError).not.toHaveBeenCalled();
});

test("shows the backend error and does not navigate when login fails", async () => {
  mockLogin.mockRejectedValue({
    response: { data: { detail: { message: "Credenciais inválidas" } } },
  });
  render(<Login />);

  await userEvent.type(screen.getByTestId("login-email"), "a@b.com");
  await userEvent.type(screen.getByTestId("login-password"), "wrong");
  await userEvent.click(screen.getByTestId("login-submit"));

  expect(await screen.findByTestId("login-error")).toHaveTextContent(/credenciais inválidas/i);
  expect(mockNavigate).not.toHaveBeenCalled();
  expect(mockToastError).toHaveBeenCalledWith("Credenciais inválidas");
});
