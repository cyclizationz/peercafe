import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';

import DeliveryNavigationPage from '../../app/(main)/user/delivery/navigation/page';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock supabase client
const mockGetUser = jest.fn();
const mockFrom = jest.fn();

jest.mock('@/utils/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getUser: mockGetUser,
    },
    from: mockFrom,
  }),
}));

// Mock NavigationMap component
jest.mock('../../app/(main)/user/delivery/NavigationMap', () => {
  return function MockNavigationMap(props: any) {
    return <div data-testid="navigation-map">Navigation Map</div>;
  };
});

describe('Delivery Navigation Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'delivery-user-1' } },
      error: null,
    });
  });

  it('renders loading state initially', async () => {
    mockFrom.mockReturnValue({
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      in: jest.fn().mockReturnThis(),
      order: jest.fn().mockReturnThis(),
      limit: jest.fn().mockResolvedValue({ data: [], error: null }),
    } as any);

    await act(async () => {
      render(<DeliveryNavigationPage />);
    });

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders no active order message when no orders found', async () => {
    mockFrom.mockReturnValue({
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      in: jest.fn().mockReturnThis(),
      order: jest.fn().mockReturnThis(),
      limit: jest.fn().mockResolvedValue({ data: [], error: null }),
    } as any);

    await act(async () => {
      render(<DeliveryNavigationPage />);
    });

    await waitFor(() => {
      expect(
        screen.getByText(/No active delivery found/i)
      ).toBeInTheDocument();
    });
  });

  it('renders active order when found', async () => {
    const mockOrder = {
      order_id: 'order-123',
      status: 'assigned',
      restaurants: {
        name: 'Test Restaurant',
        address: '123 Main St',
      },
    };

    mockFrom.mockReturnValue({
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      in: jest.fn().mockReturnThis(),
      order: jest.fn().mockReturnThis(),
      limit: jest.fn().mockResolvedValue({ data: [mockOrder], error: null }),
    } as any);

    await act(async () => {
      render(<DeliveryNavigationPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('Test Restaurant')).toBeInTheDocument();
      expect(screen.getByText(/Order #order-123/i)).toBeInTheDocument();
      expect(screen.getByText(/Status: ASSIGNED/i)).toBeInTheDocument();
    });
  });

  it('shows error when user is not authenticated', async () => {
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: { message: 'Not authenticated' },
    });

    mockFrom.mockReturnValue({
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      in: jest.fn().mockReturnThis(),
      order: jest.fn().mockReturnThis(),
      limit: jest.fn().mockResolvedValue({ data: [], error: null }),
    } as any);

    await act(async () => {
      render(<DeliveryNavigationPage />);
    });

    await waitFor(() => {
      expect(
        screen.getByText(/Please log in to access navigation/i)
      ).toBeInTheDocument();
    });
  });

  it('handles order status update', async () => {
    const mockOrder = {
      order_id: 'order-123',
      status: 'assigned',
      restaurants: {
        name: 'Test Restaurant',
        address: '123 Main St',
      },
    };

    mockFrom.mockReturnValue({
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      in: jest.fn().mockReturnThis(),
      order: jest.fn().mockReturnThis(),
      limit: jest.fn().mockResolvedValue({ data: [mockOrder], error: null }),
    } as any);

    await act(async () => {
      render(<DeliveryNavigationPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('Test Restaurant')).toBeInTheDocument();
    });

    // The component should handle order updates through the NavigationMap callback
    expect(screen.getByTestId('navigation-map')).toBeInTheDocument();
  });
});

