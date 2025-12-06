import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';

import ChatPage from '../../app/(main)/admin/chat/page';
import { CartProvider } from '../../app/_contexts/CartContext';

// Mock supabase client
const mockGetUser = jest.fn();
jest.mock('@/utils/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getUser: mockGetUser,
    },
    from: () => ({
      select: () => ({
        eq: () => ({
          single: async () => ({
            data: { id: 'u-test', name: 'Test User' },
            error: null,
          }),
        }),
      }),
    }),
  }),
}));

describe('Admin Chat Page', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'u-test' } },
      error: null,
    });
  });

  it('renders chat page', async () => {
    await act(async () => {
      render(
        <CartProvider>
          <ChatPage />
        </CartProvider>
      );
    });

    await waitFor(() => {
      expect(
        screen.getByText(/Chat with our AI to find the perfect restaurant/i)
      ).toBeInTheDocument();
    });
  });

  it('renders input field', async () => {
    await act(async () => {
      render(
        <CartProvider>
          <ChatPage />
        </CartProvider>
      );
    });

    await waitFor(() => {
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });
  });

  it('renders send button', async () => {
    await act(async () => {
      render(
        <CartProvider>
          <ChatPage />
        </CartProvider>
      );
    });

    await waitFor(() => {
      // Verify input field exists (send button should be next to it)
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      
      // Verify there are buttons on the page (one should be the send button)
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
      
      // The send button should be an IconButton, check for buttons with SVG icons
      const iconButtons = buttons.filter(button => button.querySelector('svg'));
      expect(iconButtons.length).toBeGreaterThan(0);
    });
  });
});
