import React from "react";
import { render, screen } from "@testing-library/react";
import Result from "./Result";

test("does not render a direct download link", () => {
  render(
    <Result
      filename="invoice.pdf"
      rowCount={12}
      totalPages={3}
      jobId="job-1"
      onReset={() => {}}
      emailState="idle"
      onSendEmail={async () => {}}
    />
  );

  expect(screen.queryByRole("link", { name: /download/i })).toBeNull();
  expect(screen.queryByRole("button", { name: /download/i })).toBeNull();
});
