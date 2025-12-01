import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MarkdownContent from '../../app/_components/MarkdownContent';

describe('MarkdownContent', () => {
  it('renders markdown text with bullet list', () => {
    const md = '# Title\n\n- Item 1\n- Item 2';
    render(<MarkdownContent content={md} />);

    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });
});


