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
  Avatar,
  IconButton,
  Chip,
  Alert,
  Divider,
  Rating,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  RestartAlt as RestartIcon,
  Lightbulb as LightbulbIcon,
  Restaurant as RestaurantIcon,
  Star as StarIcon,
  AttachMoney as MoneyIcon,
  EventAvailable as ReservationIcon,
  Deck as OutdoorIcon,
} from '@mui/icons-material';
import Navbar from '../../../_components/navbar';

// API Base URL - note the /ai prefix for AI routes
const API_BASE = 'http://localhost:8000/api/ai';

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};

type RestaurantData = {
  name?: string;
  cuisine?: string;
  location?: string;
  price_range?: string;
  rating?: number;
  takes_reservations?: string;
  outdoor_seating?: string;
};

// Function to parse bucket tags from AI response
function parseRestaurantBuckets(content: string): {
  text: string;
  restaurants: RestaurantData[];
} {
  const bucketRegex = /<bucket="restaurant_database">(.*?)<\/bucket>/g;
  const restaurants: RestaurantData[] = [];
  
  let match;
  while ((match = bucketRegex.exec(content)) !== null) {
    try {
      // Fix malformed JSON (missing quotes)
      let jsonStr = match[1]
        .replace(/(\w+):/g, '"$1":')
        .replace(/: "(\$+),/g, ': "$1",'); // Fix price range missing quote
      
      const data = JSON.parse(jsonStr);
      restaurants.push(data);
    } catch (e) {
      console.error('Error parsing bucket:', e);
    }
  }
  
  // Remove bucket tags from text
  const cleanText = content.replace(bucketRegex, '').trim();
  
  return { text: cleanText, restaurants };
}

export default function ChatPage() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to get response');
      }

      const data = await res.json();
      
      // Store session ID from first response
      if (!sessionId && data.session_id) {
        setSessionId(data.session_id);
      }

      const botMsg: ChatMessage = {
        role: 'assistant',
        content: data.response,
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Error contacting server.'
      );
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const resetChat = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_BASE}/chat/reset`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId }),
        });
      } catch (err) {
        console.error('Error resetting chat:', err);
      }
    }
    
    setMessages([]);
    setSessionId(null);
    setError(null);
    setInput('');
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      <Navbar />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Paper elevation={2} sx={{ p: 4, mb: 4, backgroundColor: '#fafafa' }}>
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Typography
              variant="h3"
              component="h1"
              fontWeight="bold"
              color="primary.main"
              gutterBottom
            >
              💬 AI Restaurant Assistant
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Chat with our AI to find the perfect restaurant
            </Typography>
          </Box>
          
          {sessionId && (
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Chip
                label={`Session: ${sessionId.substring(0, 8)}...`}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Box>
          )}
        </Paper>

        <Box sx={{ maxWidth: 900, mx: 'auto' }}>
          {/* Example Prompts - Show only when no messages */}
          {messages.length === 0 && (
            <Card sx={{ mb: 3, border: '1px solid #e0e0e0' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <LightbulbIcon
                    sx={{ color: 'warning.main', mr: 1, fontSize: 24 }}
                  />
                  <Typography variant="h6" fontWeight="bold">
                    Start a conversation:
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
          )}

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Chat Messages */}
          <Paper
            elevation={2}
            sx={{
              p: 3,
              mb: 3,
              minHeight: '500px',
              maxHeight: '600px',
              overflowY: 'auto',
              backgroundColor: '#fafafa',
              border: '1px solid #e0e0e0',
            }}
          >
            {messages.length === 0 ? (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: 'text.secondary',
                }}
              >
                <BotIcon sx={{ fontSize: 80, mb: 2, opacity: 0.3 }} />
                <Typography variant="h6" color="text.secondary">
                  Start a conversation to get restaurant recommendations
                </Typography>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {messages.map((msg, i) => {
                  const { text, restaurants } = msg.role === 'assistant' 
                    ? parseRestaurantBuckets(msg.content)
                    : { text: msg.content, restaurants: [] };

                  return (
                    <Box key={i}>
                      <Box
                        sx={{
                          display: 'flex',
                          flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                          alignItems: 'flex-start',
                          gap: 1,
                        }}
                      >
                        <Avatar
                          sx={{
                            bgcolor: msg.role === 'user' ? 'primary.main' : 'secondary.main',
                            width: 40,
                            height: 40,
                          }}
                        >
                          {msg.role === 'user' ? (
                            <PersonIcon />
                          ) : (
                            <BotIcon />
                          )}
                        </Avatar>
                        <Paper
                          elevation={1}
                          sx={{
                            p: 2,
                            maxWidth: restaurants.length > 0 ? '100%' : '75%',
                            backgroundColor:
                              msg.role === 'user' ? 'primary.light' : 'white',
                            borderRadius: 2,
                            flex: restaurants.length > 0 ? 1 : 'initial',
                          }}
                        >
                          <Typography
                            variant="body1"
                            sx={{
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              color: msg.role === 'user' ? 'white' : 'text.primary',
                              mb: restaurants.length > 0 ? 2 : 0,
                            }}
                          >
                            {text}
                          </Typography>

                          {/* Restaurant Cards */}
                          {restaurants.length > 0 && (
                            <Box
                              sx={{
                                display: 'grid',
                                gridTemplateColumns: {
                                  xs: '1fr',
                                  sm: 'repeat(2, 1fr)',
                                  md: 'repeat(3, 1fr)',
                                },
                                gap: 2,
                                mt: 1,
                              }}
                            >
                              {restaurants.map((restaurant, idx) => (
                                <Card
                                  key={idx}
                                  sx={{
                                    height: '100%',
                                    border: '1px solid #e0e0e0',
                                    transition: 'transform 0.2s',
                                    '&:hover': {
                                      transform: 'translateY(-2px)',
                                      boxShadow: 3,
                                    },
                                  }}
                                >
                                  <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                      <RestaurantIcon
                                        sx={{ color: 'primary.main', mr: 1 }}
                                      />
                                      <Typography
                                        variant="h6"
                                        component="div"
                                        fontWeight="bold"
                                        noWrap
                                      >
                                        {restaurant.name || 'Restaurant'}
                                      </Typography>
                                    </Box>

                                    {restaurant.rating && (
                                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        <Rating
                                          value={restaurant.rating}
                                          readOnly
                                          size="small"
                                          precision={0.1}
                                        />
                                        <Typography
                                          variant="body2"
                                          color="text.secondary"
                                          sx={{ ml: 1 }}
                                        >
                                          {restaurant.rating}
                                        </Typography>
                                      </Box>
                                    )}

                                    <Divider sx={{ my: 1.5 }} />

                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                      {restaurant.cuisine && (
                                        <Chip
                                          label={restaurant.cuisine}
                                          size="small"
                                          sx={{ alignSelf: 'flex-start', mb: 1 }}
                                        />
                                      )}

                                      {restaurant.price_range && (
                                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                          <MoneyIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                                          <Typography variant="body2" color="text.secondary">
                                            {restaurant.price_range}
                                          </Typography>
                                        </Box>
                                      )}

                                      {restaurant.takes_reservations && (
                                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                          <ReservationIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                                          <Typography variant="body2" color="text.secondary">
                                            Reservations: {restaurant.takes_reservations === 'true' ? 'Yes' : 'No'}
                                          </Typography>
                                        </Box>
                                      )}

                                      {restaurant.outdoor_seating && (
                                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                          <OutdoorIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                                          <Typography variant="body2" color="text.secondary">
                                            Outdoor: {restaurant.outdoor_seating === 'true' ? 'Yes' : 'No'}
                                          </Typography>
                                        </Box>
                                      )}
                                    </Box>
                                  </CardContent>
                                </Card>
                              ))}
                            </Box>
                          )}
                        </Paper>
                      </Box>
                    </Box>
                  );
                })}
                {loading && (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 1,
                    }}
                  >
                    <Avatar
                      sx={{
                        bgcolor: 'secondary.main',
                        width: 40,
                        height: 40,
                      }}
                    >
                      <BotIcon />
                    </Avatar>
                    <Paper
                      elevation={1}
                      sx={{
                        p: 2,
                        backgroundColor: 'white',
                        borderRadius: 2,
                      }}
                    >
                      <Typography variant="body1" color="text.secondary">
                        Thinking...
                      </Typography>
                    </Paper>
                  </Box>
                )}
                <div ref={messagesEndRef} />
              </Box>
            )}
          </Paper>

          {/* Input Section */}
          <Card sx={{ border: '1px solid #e0e0e0' }}>
            <CardContent>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  placeholder="Type your message... (Press Enter to send)"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  variant="outlined"
                  disabled={loading}
                />
                <IconButton
                  color="primary"
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': { bgcolor: 'primary.dark' },
                    '&.Mui-disabled': { bgcolor: 'grey.300' },
                  }}
                >
                  <SendIcon />
                </IconButton>
                {messages.length > 0 && (
                  <IconButton
                    color="secondary"
                    onClick={resetChat}
                    disabled={loading}
                    sx={{
                      border: '1px solid',
                      borderColor: 'secondary.main',
                    }}
                  >
                    <RestartIcon />
                  </IconButton>
                )}
              </Box>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mt: 1 }}
              >
                Press Enter to send • Shift+Enter for new line
              </Typography>
            </CardContent>
          </Card>

          {/* Footer Info */}
          <Box sx={{ mt: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              💡 The AI remembers your conversation context for better recommendations
            </Typography>
          </Box>
        </Box>
      </Container>
    </>
  );
}