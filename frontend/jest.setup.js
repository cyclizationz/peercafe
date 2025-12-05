// Optional: configure or set up a testing framework before each test.
// If you delete this file, remove `setupFilesAfterEnv` from `jest.config.js`

// Used for __tests__/testing-library.js
// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Polyfill TextEncoder/TextDecoder for Node/JSDOM environments
if (typeof global.TextEncoder === 'undefined') {
  const { TextEncoder, TextDecoder } = require('util');
  global.TextEncoder = TextEncoder;
  global.TextDecoder = TextDecoder;
}

// Minimal WHATWG Request/Response/Headers polyfill for Jest environment
if (typeof global.Request === 'undefined') {
  class HeadersPoly {
    constructor(init = {}) {
      this.map = new Map();
      if (init && typeof init === 'object') {
        for (const key of Object.keys(init)) {
          this.map.set(String(key).toLowerCase(), String(init[key]));
        }
      }
    }
    get(k) {
      return this.map.get(String(k).toLowerCase()) || null;
    }
    append(k, v) {
      this.map.set(String(k).toLowerCase(), String(v));
    }
    has(k) {
      return this.map.has(String(k).toLowerCase());
    }
  }

  class RequestPoly {
    constructor(input, init = {}) {
      if (typeof input === 'string') {
        this.url = input;
      } else if (input && input.url) {
        this.url = input.url;
      } else {
        this.url = '';
      }
      this.method = (init && init.method) || (input && input.method) || 'GET';
      this.headers = new HeadersPoly(
        (init && init.headers) || (input && input.headers) || {}
      );
      this.body = init && init.body ? init.body : null;
    }
  }

  class ResponsePoly {
    constructor(body = null, init = {}) {
      this._body = body;
      this.status = init.status || 200;
      this.headers = new HeadersPoly(init.headers || {});
    }
    async json() {
      if (typeof this._body === 'string') return JSON.parse(this._body);
      return this._body;
    }
    async text() {
      if (this._body == null) return '';
      return typeof this._body === 'string'
        ? this._body
        : JSON.stringify(this._body);
    }
  }

  global.Headers = HeadersPoly;
  global.Request = RequestPoly;
  global.Response = ResponsePoly;
}

// Ensure a mockable global.fetch exists for tests
if (typeof global.fetch === 'undefined') {
  // Use a jest mock so tests can spyOn/replace it
  global.fetch = (..._args) => Promise.resolve(new global.Response(null));
}

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn().mockResolvedValue(undefined),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
      isFallback: false,
    };
  },
}));

// Mock Next.js navigation (App Router)
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    };
  },
  useSearchParams() {
    return new URLSearchParams();
  },
  usePathname() {
    return '/';
  },
}));

// Mock environment variables
process.env.NODE_ENV = 'test';

// Mock react-markdown to avoid ES module parsing issues
jest.mock('react-markdown', () => {
  const React = require('react');
  return function ReactMarkdown({ children }) {
    // Simple markdown processor: just render the content
    // This is enough for most tests that just check if text is present
    return React.createElement(React.Fragment, null, children);
  };
});
