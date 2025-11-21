import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AdminInventoryPage from '../../app/(main)/admin/inventory/page';

// Mock Navbar
jest.mock('../../app/_components/navbar', () => {
  return function MockNavbar() {
    return <div data-testid="navbar">Mock Navbar</div>;
  };
});

// Global fetch mock
global.fetch = jest.fn();

const sampleSnapshot = {
  generated_at: new Date().toISOString(),
  items: [
    {
      item_id: 1,
      restaurant_id: 1,
      item_name: 'Test Item',
      description: 'Tasty',
      is_available: true,
      price: 10,
      stock_quantity: 5,
      reorder_threshold: 10,
      reorder_quantity: 20,
      lead_time_days: 3,
      is_promo: false,
      promo_note: null,
      last_sales_7d: 1,
      last_sales_30d: 2,
    },
  ],
  low_stock_items: [
    {
      item: {
        item_id: 1,
        restaurant_id: 1,
        item_name: 'Test Item',
        description: 'Tasty',
        is_available: true,
        price: 10,
        stock_quantity: 5,
        reorder_threshold: 10,
        reorder_quantity: 20,
        lead_time_days: 3,
        is_promo: false,
        promo_note: null,
        last_sales_7d: 1,
        last_sales_30d: 2,
      },
      shortage: 5,
    },
  ],
  overstock_items: [],
  stagnant_items: [],
};

describe('AdminInventoryPage', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockReset();
  });

  it('renders navbar and basic layout', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => sampleSnapshot,
    });

    render(<AdminInventoryPage />);

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(
      await screen.findByText(/Inventory Management/i)
    ).toBeInTheDocument();
  });

  it('shows empty state when no items', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...sampleSnapshot,
        items: [],
        low_stock_items: [],
        overstock_items: [],
        stagnant_items: [],
      }),
    });

    render(<AdminInventoryPage />);

    expect(
      await screen.findByText(/No inventory data available/i)
    ).toBeInTheDocument();
  });

  it('calls analysis, refill, and promo endpoints on button clicks', async () => {
    // initial status
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => sampleSnapshot,
    });

    render(<AdminInventoryPage />);
    await screen.findByText('Test Item');

    // analysis
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, analysis: 'Analysis text' }),
    });
    fireEvent.click(
      screen.getByRole('button', { name: /AI Inventory Analysis/i })
    );
    await waitFor(() =>
      expect(screen.getByText(/Analysis text/i)).toBeInTheDocument()
    );

    // refill
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, plan: 'Plan text' }),
    });
    fireEvent.click(screen.getByRole('button', { name: /Refill Plan/i }));
    await waitFor(() =>
      expect(screen.getByText(/Plan text/i)).toBeInTheDocument()
    );

    // promo
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, suggestions: 'Promo text' }),
    });
    fireEvent.click(
      screen.getByRole('button', { name: /Promo Suggestions/i })
    );
    await waitFor(() =>
      expect(screen.getByText(/Promo text/i)).toBeInTheDocument()
    );
  });
});


