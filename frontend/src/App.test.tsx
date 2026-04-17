import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders branded landing copy", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: /pdf to csv/i })).toBeInTheDocument();
  expect(screen.getByText(/delivered by email/i, { selector: ".hero-copy" })).toBeInTheDocument();
});
