import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

vi.mock('./api/client', () => ({
  uploadPdf: vi.fn(),
  pollStatus: vi.fn(),
  sendEmail: vi.fn(),
}));

vi.mock('./components/TurnstileWidget', () => ({
  default: () => <div data-testid="turnstile-mock" />,
}));

describe('App layout', () => {
  it('does not render a hero-panel', () => {
    render(<App />);
    expect(document.querySelector('.hero-panel')).toBeNull();
  });

  it('renders the workspace-panel', () => {
    render(<App />);
    expect(document.querySelector('.workspace-panel')).not.toBeNull();
  });
});
