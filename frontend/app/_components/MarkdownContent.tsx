import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import { Typography } from '@mui/material';

interface MarkdownContentProps {
  content: string;
}

export default function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <Typography
      component="div"
      sx={{
        '& p': { margin: '0 0 0.5rem 0' },
        '& ul, & ol': { paddingLeft: '1.5rem', margin: '0 0 0.5rem 0' },
        '& li': { marginBottom: '0.25rem' },
      }}
    >
      <ReactMarkdown>{content}</ReactMarkdown>
    </Typography>
  );
}
