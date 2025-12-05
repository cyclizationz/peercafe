'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navbar from '../../../_components/navbar';

// Creating a supabase client to access user id and assign orders
import { createClient } from '@/utils/supabase/client';

const backend_url =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface PointsData {
  loyalty_points: number;
}

interface HistoryItem {
  id: string | number;
  created_at: string;
  description?: string;
  points_earned: number;
  points_balance: number;
}

const supabase = createClient();

export default function LoyaltyPointsPage() {
  const [pointsData, setPointsData] = useState<PointsData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Resolve current user ID from localStorage or backend `/api/auth/me`
  const [userId, setUserId] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = React.useState<any>(null);
  const [authLoading, setAuthLoading] = useState<boolean>(false);
  const [userLoading, setUserLoading] = useState<boolean>(true);

  const getCurrentUser = async () => {
    try {
      setAuthLoading(true);

      // Get current authenticated user
      const {
        data: { user },
        error: authError,
      } = await supabase.auth.getUser();

      if (authError || !user) {
        alert('Please log in to access the delivery page.');
        return;
      }

      // Get user details from users table
      const { data: userData, error: userError } = await supabase
        .from('users')
        .select('*')
        .eq('user_id', user.id)
        .single();

      if (userError || !userData) {
        alert('Error loading user profile.');
        return;
      }

      setCurrentUser(userData);
      setUserId(user.id);
    } catch {
      alert('Authentication error. Please try logging in again.');
    } finally {
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    getCurrentUser();
    if (!userId) return;
    fetchPointsData();
    fetchPointsHistory();
  }, [userId]);

  const fetchPointsData = async () => {
    try {
      axios
        .get(`${backend_url}/${userId}/loyalty-points`)
        .then(response => {
          const data = response.data;
          setPointsData(data);
        })
        .catch(error => {
          // eslint-disable-next-line no-console
          console.error('Error fetching points data:', error);
        });
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching points data:', error);
    }
  };

  const fetchPointsHistory = async () => {
    try {
      const response = await axios
        .get(`${backend_url}/${userId}/loyalty-points/history`)
        .then(response => {
          const data = response.data;
          setHistory(Array.isArray(data) ? data : []);
          setLoading(false);
        })
        .catch(error => {
          // eslint-disable-next-line no-console
          console.error('Error fetching points history:', error);
          setLoading(false);
        });
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching points history:', error);
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        <h1
          style={{ fontSize: '2.5rem', color: '#2563eb', marginBottom: '30px' }}
        >
          🏆 My Loyalty Points
        </h1>

        {/* Points Summary */}
        {pointsData && (
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              padding: '30px',
              border: '2px solid #e2e8f0',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              marginBottom: '30px',
              textAlign: 'center',
            }}
          >
            <h2 style={{ color: '#64748b', marginBottom: '10px' }}>
              Current Balance
            </h2>
            <div
              style={{ fontSize: '3rem', fontWeight: 'bold', color: '#16a34a' }}
            >
              {pointsData.loyalty_points} points
            </div>
            <p style={{ color: '#94a3b8', marginTop: '10px' }}>
              Earned from successful deliveries
            </p>
          </div>
        )}

        {/* Points History */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            padding: '30px',
            border: '2px solid #e2e8f0',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          <h2 style={{ color: '#2563eb', marginBottom: '20px' }}>
            Points History
          </h2>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div>Loading history...</div>
            </div>
          ) : history.length === 0 ? (
            <div
              style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}
            >
              <div style={{ fontSize: '3rem', marginBottom: '10px' }}>📊</div>
              <p>No points history yet. Start delivering to earn rewards!</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                    <th
                      style={{
                        padding: '12px',
                        textAlign: 'left',
                        color: '#2b323bff',
                      }}
                    >
                      Date
                    </th>
                    <th
                      style={{
                        padding: '12px',
                        textAlign: 'left',
                        color: '#2b323bff',
                      }}
                    >
                      Description
                    </th>
                    <th
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        color: '#2b323bff',
                      }}
                    >
                      Points
                    </th>
                    <th
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        color: '#2b323bff',
                      }}
                    >
                      Balance
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((transaction, index) => (
                    <tr
                      key={transaction.id}
                      style={{
                        borderBottom:
                          index < history.length - 1
                            ? '1px solid #f1f5f9'
                            : 'none',
                      }}
                    >
                      <td style={{ padding: '12px', color: '#2b323bff' }}>
                        {new Date(transaction.created_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '12px', color: '#2b323bff' }}>
                        {transaction.description ||
                          'Points earned from delivery'}
                      </td>
                      <td
                        style={{
                          padding: '12px',
                          textAlign: 'right',
                          color:
                            transaction.points_earned > 0
                              ? '#16a34a'
                              : '#dc2626',
                          fontWeight: 'bold',
                        }}
                      >
                        {transaction.points_earned > 0 ? '+' : ''}
                        {transaction.points_earned}
                      </td>
                      <td
                        style={{
                          padding: '12px',
                          textAlign: 'right',
                          color: '#2b323bff',
                        }}
                      >
                        {transaction.points_balance}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

