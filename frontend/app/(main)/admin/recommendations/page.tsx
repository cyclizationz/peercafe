'use client';

import * as React from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Paper,
  Alert,
  CircularProgress,
  Skeleton,
} from '@mui/material';
import {
  Restaurant as RestaurantIcon,
  Send as SendIcon,
  Lightbulb as LightbulbIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import Navbar from '../../../_components/navbar';
import MarkdownContent from '../../../_components/MarkdownContent';

// Temporary: hardcode the API base URL for testing
const API_BASE = 'http://localhost:8000/api';

export default function RecommendPage() {
  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  async function getRecommendation() {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/ai/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      // Check content type before parsing
      const contentType = res.headers.get('content-type');
      
      if (!res.ok) {
        // Try to parse error response
        if (contentType && contentType.includes('application/json')) {
          const data = await res.json();
          throw new Error(data.detail || `API Error: ${res.status} ${res.statusText}`);
        } else {
          // If HTML or other format, show more helpful error
          const text = await res.text();
          console.error('Non-JSON response:', text.substring(0, 200));
          throw new Error(
            `API endpoint returned ${res.status}. The endpoint might not exist or is returning HTML instead of JSON. Check your API route at /api/recommendations.`
          );
        }
      }

      // Parse successful response
      if (contentType && contentType.includes('application/json')) {
        const data = await res.json();
        setResult(data.recommendation);
      } else {
        throw new Error('API returned non-JSON response. Check your API endpoint configuration.');
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : 'Something went wrong.'
      );
    } finally {
      setLoading(false);
    }
  }

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && event.ctrlKey) {
      getRecommendation();
    }
  };

  return (
    <>
      <Navbar />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Paper elevation={2} sx={{ p: 4, mb: 4, backgroundColor: '#fafafa' }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Typography
              variant="h3"
              component="h1"
              fontWeight="bold"
              color="primary.main"
              gutterBottom
            >
              🤖 AI Restaurant Recommender
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Get personalized restaurant recommendations powered by AI
            </Typography>
          </Box>
          <Alert severity="info">
            AI-generated recommendations may be inaccurate or incomplete. Always
            double-check important decisions against your own data and judgment.
          </Alert>
        </Paper>

        {/* Main Content */}
        <Box sx={{ maxWidth: 800, mx: 'auto' }}>
          {/* Example Prompts */}
          <Card sx={{ mb: 3, border: '1px solid #e0e0e0' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <LightbulbIcon
                  sx={{ color: 'warning.main', mr: 1, fontSize: 24 }}
                />
                <Typography variant="h6" fontWeight="bold">
                  Try asking:
                </Typography>
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1,
                  pl: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  • "Recommend Italian food in Raleigh"
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • "I want cheap chinese food"
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • "Expensive American restaurants in Raleigh"
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • "Find me some expensive seafood"
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Input Section */}
          <Card sx={{ mb: 3, border: '1px solid #e0e0e0' }}>
            <CardContent>
              <Typography
                variant="subtitle1"
                fontWeight="bold"
                gutterBottom
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                <AutoAwesomeIcon sx={{ mr: 1, color: 'primary.main' }} />
                What are you craving?
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={4}
                placeholder="Example: Recommend Italian in Raleigh"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={handleKeyPress}
                variant="outlined"
                sx={{ mb: 2 }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  Press Ctrl+Enter to submit
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                  onClick={getRecommendation}
                  disabled={loading || !query.trim()}
                >
                  {loading ? 'Thinking...' : 'Get Recommendation'}
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Loading State */}
          {loading && (
            <Card sx={{ border: '1px solid #e0e0e0' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
                  <Skeleton variant="text" width="60%" height={32} />
                </Box>
                <Skeleton variant="text" width="100%" />
                <Skeleton variant="text" width="100%" />
                <Skeleton variant="text" width="90%" />
                <Skeleton variant="text" width="95%" />
                <Skeleton variant="text" width="80%" />
              </CardContent>
            </Card>
          )}

          {/* Result Display */}
          {result && !loading && (
            <Card
              sx={{
                border: '2px solid',
                borderColor: 'primary.main',
                backgroundColor: '#f8f9ff',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <RestaurantIcon
                    sx={{ color: 'primary.main', mr: 1, fontSize: 28 }}
                  />
                  <Typography variant="h5" fontWeight="bold" color="primary.main">
                    Your Personalized Recommendation
                  </Typography>
                </Box>
                <MarkdownContent content={result} />
                <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e0e0e0' }}>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setQuery('');
                      setResult(null);
                      setError(null);
                    }}
                  >
                    New Search
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Footer Info */}
          {!loading && !result && (
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                💡 Our AI analyzes restaurant data to provide personalized recommendations
              </Typography>
            </Box>
          )}
        </Box>
      </Container>
    </>
  );
}