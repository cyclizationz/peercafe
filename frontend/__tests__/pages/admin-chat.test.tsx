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
      expect(screen.getByText(/Chat with AI/i)).toBeInTheDocument();
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
      const sendButton = screen.getByRole('button', { name: /Send/i });
      expect(sendButton).toBeInTheDocument();
    });
  });
});

