'use client';

import * as React from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Breadcrumbs,
  Link,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Button,
  Snackbar,
  Alert,
} from '@mui/material';
import Navbar from '../../../_components/navbar';
import MarkdownContent from '../../../_components/MarkdownContent';
import { API_BASE } from '@/utils/api';

interface InventoryItem {
  item_id: number;
  restaurant_id: number;
  item_name: string;
  description?: string | null;
  is_available: boolean;
  price: number;
  quantity: number;
  reorder_threshold: number;
  reorder_quantity: number;
  lead_time_days: number;
  is_promo: boolean;
  promo_note?: string | null;
  last_sales_7d: number;
  last_sales_30d: number;
}

interface LowStockItem {
  item: InventoryItem;
  shortage: number;
}

interface OverstockItem {
  item: InventoryItem;
  overstock_units: number;
}

interface StagnantItem {
  item: InventoryItem;
  days_without_sales: number;
}

interface InventorySnapshot {
  generated_at: string;
  items: InventoryItem[];
  low_stock_items: LowStockItem[];
  overstock_items: OverstockItem[];
  stagnant_items: StagnantItem[];
}

export default function AdminInventoryPage() {
  const [snapshot, setSnapshot] = React.useState<InventorySnapshot | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [analysisLoading, setAnalysisLoading] = React.useState(false);
  const [refillLoading, setRefillLoading] = React.useState(false);
  const [promoLoading, setPromoLoading] = React.useState(false);
  const [analysisText, setAnalysisText] = React.useState<string | null>(null);
  const [refillPlan, setRefillPlan] = React.useState<string | null>(null);
  const [promoSuggestions, setPromoSuggestions] = React.useState<string | null>(
    null
  );
  const [snackbar, setSnackbar] = React.useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error',
  });

  React.useEffect(() => {
    fetchSnapshot();
  }, []);

  const fetchSnapshot = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/ai/inventory/status`);
      if (!res.ok) throw new Error('Failed to fetch inventory status');
      const data = (await res.json()) as InventorySnapshot;
      setSnapshot(data);
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: err.message || 'Failed to load inventory',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const callAiEndpoint = async (
    path: string,
    setText: (value: string | null) => void,
    setLoadingFlag: (value: boolean) => void,
    fieldName: 'analysis' | 'plan' | 'suggestions'
  ) => {
    setLoadingFlag(true);
    try {
      const res = await fetch(`${API_BASE}/ai/${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `Failed to call ${path}`);
      }
      setText(data[fieldName] || '');
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: err.message || 'AI request failed',
        severity: 'error',
      });
    } finally {
      setLoadingFlag(false);
    }
  };

  const highlightRow = (item: InventoryItem) => {
    const isLow =
      snapshot?.low_stock_items.some(ls => ls.item.item_id === item.item_id) ||
      false;
    const isOver =
      snapshot?.overstock_items.some(os => os.item.item_id === item.item_id) ||
      false;
    if (isLow) return '#fef2f2'; // light red
    if (isOver) return '#eff6ff'; // light blue
    return 'inherit';
  };

  return (
    <>
      <Navbar />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link
            color="inherit"
            href="/admin/dashboard"
            sx={{
              display: 'flex',
              alignItems: 'center',
              textDecoration: 'none',
            }}
          >
            Admin Dashboard
          </Link>
          <Typography color="text.primary">Inventory</Typography>
        </Breadcrumbs>

        <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 3,
            }}
          >
            <Typography variant="h4" color="primary.main" fontWeight="bold">
              Inventory Management
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                onClick={fetchSnapshot}
                disabled={loading}
              >
                Refresh
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={() =>
                  callAiEndpoint(
                    'inventory/analysis',
                    setAnalysisText,
                    setAnalysisLoading,
                    'analysis'
                  )
                }
                disabled={analysisLoading}
              >
                {analysisLoading ? 'Analyzing…' : 'AI Inventory Analysis'}
              </Button>
            </Box>
          </Box>

          <Divider sx={{ mb: 3 }} />

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : !snapshot || snapshot.items.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No inventory data available
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Add menu items for your restaurants to start tracking inventory.
              </Typography>
            </Box>
          ) : (
            <>
              <Box
                sx={{
                  display: 'flex',
                  gap: 2,
                  mb: 3,
                  flexWrap: 'wrap',
                }}
              >
                <Chip
                  label={`Items: ${snapshot.items.length}`}
                  color="default"
                />
                <Chip
                  label={`Low stock: ${snapshot.low_stock_items.length}`}
                  color={
                    snapshot.low_stock_items.length > 0
                      ? 'error'
                      : 'success'
                  }
                />
                <Chip
                  label={`Overstock: ${snapshot.overstock_items.length}`}
                  color={
                    snapshot.overstock_items.length > 0
                      ? 'warning'
                      : 'default'
                  }
                />
                <Chip
                  label={`Stagnant: ${snapshot.stagnant_items.length}`}
                  color={
                    snapshot.stagnant_items.length > 0
                      ? 'warning'
                      : 'default'
                  }
                />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                  Snapshot generated at:{' '}
                  {new Date(snapshot.generated_at).toLocaleString()}
                </Typography>
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                      <TableCell>
                        <strong>Item</strong>
                      </TableCell>
                      <TableCell>
                        <strong>Restaurant ID</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>Price</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>Stock</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>Reorder @</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>Reorder Qty</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>Lead Time (d)</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>Sales 7d</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>Sales 30d</strong>
                      </TableCell>
                      <TableCell>
                        <strong>Status</strong>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {snapshot.items.map(item => (
                      <TableRow
                        key={item.item_id}
                        sx={{ backgroundColor: highlightRow(item) }}
                      >
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {item.item_name}
                          </Typography>
                          {item.description && (
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              display="block"
                            >
                              {item.description}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>{item.restaurant_id}</TableCell>
                        <TableCell align="right">
                          ${item.price.toFixed(2)}
                        </TableCell>
                        <TableCell align="right">{item.quantity}</TableCell>
                        <TableCell align="right">
                          {item.reorder_threshold}
                        </TableCell>
                        <TableCell align="right">
                          {item.reorder_quantity}
                        </TableCell>
                        <TableCell align="right">
                          {item.lead_time_days}
                        </TableCell>
                        <TableCell align="right">
                          {item.last_sales_7d}
                        </TableCell>
                        <TableCell align="right">
                          {item.last_sales_30d}
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            <Chip
                              size="small"
                              label={item.is_available ? 'Available' : 'Unavailable'}
                              color={item.is_available ? 'success' : 'default'}
                            />
                            {snapshot.low_stock_items.some(
                              ls => ls.item.item_id === item.item_id
                            ) && (
                              <Chip
                                size="small"
                                label="Low stock"
                                color="error"
                                variant="outlined"
                              />
                            )}
                            {snapshot.overstock_items.some(
                              os => os.item.item_id === item.item_id
                            ) && (
                              <Chip
                                size="small"
                                label="Overstock"
                                color="warning"
                                variant="outlined"
                              />
                            )}
                            {snapshot.stagnant_items.some(
                              st => st.item.item_id === item.item_id
                            ) && (
                              <Chip
                                size="small"
                                label="Stagnant"
                                color="warning"
                                variant="outlined"
                              />
                            )}
                            {item.is_promo && (
                              <Chip
                                size="small"
                                label="Promo"
                                color="primary"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </Paper>

        <Paper elevation={3} sx={{ p: 4 }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 3,
            }}
          >
            <Typography variant="h5" color="primary.main" fontWeight="bold">
              AI Suggestions
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button variant="text" href="/admin/chat">
                Open AI Chat
              </Button>
              <Button
                variant="contained"
                color="secondary"
                onClick={() =>
                  callAiEndpoint(
                    'inventory/refill-plan',
                    setRefillPlan,
                    setRefillLoading,
                    'plan'
                  )
                }
                disabled={refillLoading}
              >
                {refillLoading ? 'Generating…' : 'Refill Plan'}
              </Button>
              <Button
                variant="outlined"
                color="secondary"
                onClick={() =>
                  callAiEndpoint(
                    'inventory/promo-suggestions',
                    setPromoSuggestions,
                    setPromoLoading,
                    'suggestions'
                  )
                }
                disabled={promoLoading}
              >
                {promoLoading ? 'Generating…' : 'Promo Suggestions'}
              </Button>
            </Box>
          </Box>
          <Alert severity="info" sx={{ mb: 3 }}>
            AI-generated inventory suggestions may be inaccurate or incomplete.
            Always review them against your own data, policies, and judgment
            before making financial or operational decisions.
          </Alert>
          <Divider sx={{ mb: 3 }} />

          <Box sx={{ display: 'grid', gap: 2 }}>
            {analysisText && (
              <Paper
                variant="outlined"
                sx={{ p: 2, backgroundColor: '#f9fafb' }}
              >
                <Typography
                  variant="subtitle1"
                  fontWeight="bold"
                  gutterBottom
                >
                  Inventory Analysis
                </Typography>
                <MarkdownContent content={analysisText} />
              </Paper>
            )}

            {refillPlan && (
              <Paper
                variant="outlined"
                sx={{ p: 2, backgroundColor: '#f0fdf4' }}
              >
                <Typography
                  variant="subtitle1"
                  fontWeight="bold"
                  gutterBottom
                >
                  Refill Plan
                </Typography>
                <MarkdownContent content={refillPlan} />
              </Paper>
            )}

            {promoSuggestions && (
              <Paper
                variant="outlined"
                sx={{ p: 2, backgroundColor: '#eff6ff' }}
              >
                <Typography
                  variant="subtitle1"
                  fontWeight="bold"
                  gutterBottom
                >
                  Promo Suggestions
                </Typography>
                <MarkdownContent content={promoSuggestions} />
              </Paper>
            )}

            {!analysisText && !refillPlan && !promoSuggestions && (
              <Typography variant="body2" color="text.secondary">
                Use the buttons above to request AI-generated insights for your
                current inventory.
              </Typography>
            )}
          </Box>
        </Paper>

        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar(s => ({ ...s, open: false }))}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            onClose={() => setSnackbar(s => ({ ...s, open: false }))}
            severity={snackbar.severity}
            variant="filled"
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </>
  );
}


