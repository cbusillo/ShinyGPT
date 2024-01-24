//ChatOutput.js
import Box from "@mui/material/Box";
import React, {useCallback, useEffect, useState} from "react";
import CodeBlock from "./CodeBlock";

const ChatOutput = ({outputText, outputContainerRef}) => {
  const [processedOutput, setProcessedOutput] = useState([]);

  const renderOutputText = useCallback((text) => {
    const elements = [];
    const codeRegex = /```(.*?)```/gs;
    const openCodeRegex = /```(.*)/s; // Regex to find opening triple tick and capture everything after it
    let lastIndex = 0;
    let result;

    while ((result = codeRegex.exec(text)) !== null) {
      const plainText = text.substring(lastIndex, result.index);
      const code = result[1];
      elements.push(<div key={`text-${lastIndex}`}>{convertLineBreaks(plainText)}</div>);
      elements.push(<CodeBlock key={`code-${lastIndex}`} code={code}/>);
      lastIndex = codeRegex.lastIndex;
    }

    const remainingText = text.substring(lastIndex);
    const openCodeMatch = openCodeRegex.exec(remainingText);
    if (openCodeMatch) {
      const beforeCode = remainingText.substring(0, openCodeMatch.index);
      const ongoingCode = openCodeMatch[1];
      elements.push(<div key={`text-${lastIndex}`}>{convertLineBreaks(beforeCode)}</div>);
      elements.push(<CodeBlock key={`code-${lastIndex}-ongoing`} code={ongoingCode} ongoing/>);
    } else {
      elements.push(<div key={`text-${lastIndex}`}>{convertLineBreaks(remainingText)}</div>);
    }

    return elements;
  }, []);

  const convertLineBreaks = (text) => {
    return text.split('\n').map((line, index) => (
      <React.Fragment key={index}>
        {line}
        <br/>
      </React.Fragment>
    ));
  };

  useEffect(() => {
    const newProcessedOutput = renderOutputText(outputText);
    setProcessedOutput(newProcessedOutput);

    const container = outputContainerRef.current;
    if (container) {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          container.scrollTop = container.scrollHeight;
        });
      });
    }
  }, [outputText, renderOutputText, outputContainerRef]);

  return (
    <Box ref={outputContainerRef} sx={{
      flexBasis: '50%',
      maxHeight: '100vh',
      overflowY: 'auto',
      border: '1px dashed grey',
      padding: '0.5em',
    }}>
      {processedOutput}
    </Box>
  )
}

export default ChatOutput;