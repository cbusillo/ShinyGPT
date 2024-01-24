import React, {useState} from 'react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import {atomOneDark as codeStyle} from 'react-syntax-highlighter/dist/esm/styles/hljs';
import Button from '@mui/material/Button';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

const CodeBlock = ({code, language}) => {
  const [copySuccess, setCopySuccess] = useState('');

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopySuccess('Copied!');
      setTimeout(() => setCopySuccess(''), 2000);
    });
  };

  return (
    <div style={{
      position: 'relative',
      backgroundColor: 'transparent',
      padding: '1em',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.25rem 1rem',
        backgroundColor: '#2c2c2c',
        borderTopLeftRadius: '0.75rem',
        borderTopRightRadius: '0.75rem',
        borderBottom: '1px solid grey'
      }}>
        <span style={{color: 'white', fontSize: '0.9rem'}}>{language}</span>
        <Button onClick={copyToClipboard} startIcon={<ContentCopyIcon/>} size="small" style={{color: 'white'}}>
          {copySuccess || 'Copy'}
        </Button>
      </div>
      <div>
        <SyntaxHighlighter
          language={language}
          style={codeStyle}
          PreTag={props => (
            <pre
              {...props}
              style={{
                ...codeStyle.hljs,
                padding: '0.75em',
                border: '0',
                margin: '0',
              }}
            >
      {props.children}
    </pre>
          )}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

export default CodeBlock;