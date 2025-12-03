import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import axios from 'axios';

import LoyaltyPage from '../../app/(main)/user/loyalty-points/page';
import { CartProvider } from '../../app/_contexts/CartContext';

// Mock supabase client before importing the page component
jest.mock('@/utils/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getUser: async () => ({ data: { user: { id: 'u-test' } }, error: null }),
    },
    from: () => ({
      select: () => ({
        eq: () => ({
          single: async () => ({ data: { id: 'u-test', name: 'Test User' }, error: null }),
        }),
      }),
    }),
  }),
}));

// Prevent jsdom navigation when anchors are clicked
const _origAnchorClick = HTMLAnchorElement.prototype.click;
beforeAll(() => {
  HTMLAnchorElement.prototype.click = function () {
    /* no-op */
  };
});
afterAll(() => {
  HTMLAnchorElement.prototype.click = _origAnchorClick;
});

describe('Loyalty Points Page', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    // Provide a current user in localStorage so the page will fetch
    localStorage.setItem('currentUser', JSON.stringify({ id: 'u-test' }));
  });

  afterEach(() => {
    localStorage.removeItem('currentUser');
  });

  it('renders heading and displays points when API returns data', async () => {
    // Mock axios for points and history
    const axiosGetMock = jest.spyOn(axios, 'get').mockImplementation((url: string) => {
      if (url.includes('/loyalty-points/history')) {
        return Promise.resolve({ data: [{ id: 1, points_earned: 10, points_balance: 10, created_at: new Date().toISOString() }] } as any);
      }
      if (url.includes('/loyalty-points')) {
        return Promise.resolve({ data: { loyalty_points: 50 } } as any);
      }
      return Promise.reject(new Error('not found'));
    });

    render(
      <CartProvider>
        <LoyaltyPage />
      </CartProvider>
    );

    expect(screen.getByText(/My Loyalty Points/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/50 points/i)).toBeInTheDocument();
    });

    axiosGetMock.mockRestore();
  });

  it('shows empty history message when none returned', async () => {
    const axiosGetMock = jest.spyOn(axios, 'get').mockImplementation((url: string) => {
      if (url.includes('/loyalty-points/history')) {
        return Promise.resolve({ data: [] } as any);
      }
      if (url.includes('/loyalty-points')) {
        return Promise.resolve({ data: { loyalty_points: 0 } } as any);
      }
      return Promise.reject(new Error('not found'));
    });

    render(
      <CartProvider>
        <LoyaltyPage />
      </CartProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/No points history yet/i)).toBeInTheDocument();
    });

    axiosGetMock.mockRestore();
  });
});
