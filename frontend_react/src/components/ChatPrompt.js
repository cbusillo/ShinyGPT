//ChatPrompt.js
import TextField from "@mui/material/TextField";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import React, {useCallback, useState} from "react";
import {TEST_PROMPT} from "../config";

const ChatPrompt = ({outputText, setOutputText, setOutputCodeText, websocketRef, connectWebsocket, selectedModel, testInput}) => {
  const [prompt, setPrompt] = useState('');

  const handleKeydown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendPrompt(prompt);
    }
  };


  const clearConversation = () => {
    setOutputText('');
    setOutputCodeText('');
  };

  const sendWSAndUpdateOutput = useCallback((data) => {
    let userPrompt = outputText ? "\n\n" : "";
    userPrompt += `User: \n${data.prompt}\n\nFastGPT: \n`;
    setOutputText(prev => prev + userPrompt);
    websocketRef.current.send(JSON.stringify(data));
    setPrompt('');
  }, [websocketRef, setOutputText, outputText]);

  const sendPrompt = useCallback((currentPrompt) => {
    if (!websocketRef.current ||
      websocketRef.current.readyState
      === WebSocket.CLOSED) {
      connectWebsocket();
    }
    let currentRequest = {"model": selectedModel, "prompt": currentPrompt, "test_input": testInput};
    if (websocketRef.current.readyState === WebSocket.CONNECTING) {
      websocketRef.current.addEventListener('open', () => {
        sendWSAndUpdateOutput(currentRequest);
      }, {once: true});
    } else if (websocketRef.current.readyState === WebSocket.OPEN) {
      sendWSAndUpdateOutput(currentRequest);
    }
  }, [websocketRef, selectedModel, testInput, connectWebsocket, sendWSAndUpdateOutput]);


  const sendTestPrompt = useCallback(() => {
    // noinspection LongLine
    sendPrompt(TEST_PROMPT);
  }, [sendPrompt]);

  return (
    <Box sx={{
      display: 'flex',
      paddingBottom: '1rem',
      paddingX: '1rem',
    }}>
      <TextField
        id="promptInput"
        label="Enter your prompt"
        multiline
        minRows={3}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeydown}
        variant="outlined"
        maxRows={10}
        sx={{
          flex: 1,
          mr: 1
        }}
      />
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        ml: 1
      }}>
        <Button onClick={() => sendPrompt(prompt)} variant="contained" sx={{mb: 1}}>Generate</Button>
        <Button onClick={clearConversation} variant="outlined" sx={{mb: 1}}>Clear Conversation</Button>
        <Button onClick={sendTestPrompt} variant="contained">Test Code</Button>
      </Box>
    </Box>
  );
}

export default ChatPrompt;