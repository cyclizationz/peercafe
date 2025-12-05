import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import MarkdownContent from '../../app/_components/MarkdownContent';

describe('MarkdownContent', () => {
  it('renders markdown content', () => {
    const md = '# Title\n\n- Item 1\n- Item 2';
    const { container } = render(<MarkdownContent content={md} />);

    // The mock ReactMarkdown just renders the children as-is (the markdown string)
    // Verify that the content is rendered in the component
    expect(container.textContent).toContain('# Title');
    expect(container.textContent).toContain('Item 1');
    expect(container.textContent).toContain('Item 2');
  });
});
