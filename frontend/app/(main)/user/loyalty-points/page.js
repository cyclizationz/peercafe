'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../../_components/navbar';

export default function LoyaltyPointsPage() {
  const [pointsData, setPointsData] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // This would come from your auth context or localStorage
  const userId = "current-user-id"; // Replace with actual user ID

  useEffect(() => {
    fetchPointsData();
    fetchPointsHistory();
  }, []);

  const fetchPointsData = async () => {
    try {
      const response = await fetch(`/api/auth/${userId}/loyalty-points`);
      const data = await response.json();
      setPointsData(data);
    } catch (error) {
      console.error('Error fetching points data:', error);
    }
  };

  const fetchPointsHistory = async () => {
    try {
      const response = await fetch(`/api/auth/${userId}/loyalty-points/history`);
      const data = await response.json();
      setHistory(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching points history:', error);
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '2.5rem', color: '#2563eb', marginBottom: '30px' }}>
          🏆 My Loyalty Points
        </h1>

        {/* Points Summary */}
        {pointsData && (
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            padding: '30px',
            border: '2px solid #e2e8f0',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            marginBottom: '30px',
            textAlign: 'center'
          }}>
            <h2 style={{ color: '#64748b', marginBottom: '10px' }}>Current Balance</h2>
            <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#16a34a' }}>
              {pointsData.loyalty_points} points
            </div>
            <p style={{ color: '#94a3b8', marginTop: '10px' }}>
              Earned from successful deliveries
            </p>
          </div>
        )}

        {/* Points History */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '30px',
          border: '2px solid #e2e8f0',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ color: '#2563eb', marginBottom: '20px' }}>Points History</h2>
          
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div>Loading history...</div>
            </div>
          ) : history.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              <div style={{ fontSize: '3rem', marginBottom: '10px' }}>📊</div>
              <p>No points history yet. Start delivering to earn rewards!</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                    <th style={{ padding: '12px', textAlign: 'left', color: '#64748b' }}>Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', color: '#64748b' }}>Description</th>
                    <th style={{ padding: '12px', textAlign: 'right', color: '#64748b' }}>Points</th>
                    <th style={{ padding: '12px', textAlign: 'right', color: '#64748b' }}>Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((transaction, index) => (
                    <tr key={transaction.id} style={{ borderBottom: index < history.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                      <td style={{ padding: '12px' }}>
                        {new Date(transaction.created_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '12px' }}>
                        {transaction.description || 'Points earned from delivery'}
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'right',
                        color: transaction.points_earned > 0 ? '#16a34a' : '#dc2626',
                        fontWeight: 'bold'
                      }}>
                        {transaction.points_earned > 0 ? '+' : ''}{transaction.points_earned}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#64748b' }}>
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