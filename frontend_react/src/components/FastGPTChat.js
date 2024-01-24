//FastGPTChat.js
import React, {useCallback, useEffect, useRef, useState} from 'react';
import Box from '@mui/material/Box';

import ChatPrompt from './ChatPrompt';
import ChatOutput from './ChatOutput';
import {API_CONFIG} from "../config";
import ModelSelector from "./ModelSelector";
import Typography from "@mui/material/Typography";
import Switch from "@mui/material/Switch";
import {FormControlLabel} from "@mui/material";


const FastGPTChat = () => {
  const [outputText, setOutputText] = useState('');
  const [outputCodeText, setOutputCodeText] = useState('');
  const outputContainerRef = useRef(null);
  const outputCodeContainerRef = useRef(null);
  const websocketRef = useRef(null);
  const [selectedModel, setSelectedModel] = useState('');
  const [testInput, setTestInput] = useState(false);

  const connectWebsocket = useCallback(() => {
    if (websocketRef.current) {
      if (websocketRef.current.readyState === WebSocket.OPEN) {
        console.log('WebSocket is already open.');
        return;
      }
      if (websocketRef.current.readyState === WebSocket.CONNECTING) {
        console.log('WebSocket is already connecting.');
        return;
      }
    }
    console.log('Attempting to connect to WebSocket');
    websocketRef.current = new WebSocket(`ws://${API_CONFIG.BASEURL}/generate`);

    websocketRef.current.onopen = () => {
      console.log('Connected to websocket');
    };

    websocketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.code) {
          setOutputCodeText(prev => (prev ? prev + "\n\n" : "") + data.code);
        } else if (data.response) {
          setOutputText(prev => prev + data.response);
        }
      } catch (error) {
        setOutputText(prev => prev + event.data);
      }
    };


    websocketRef.current.onclose = (event) => {
      console.log('Connection closed', event);
    };

    websocketRef.current.onerror = (event) => {
      console.log('Connection error', event);
      websocketRef.current.close();
    };
  }, []);

  useEffect(() => {
    connectWebsocket();
    return () => {
    };
  }, [connectWebsocket]);

  function handleTestInputChange() {
    setTestInput(!testInput);
  }

  return (
    <Box sx={{display: 'flex', flexDirection: 'column', height: '96vh'}}>
      <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 1}}>
        <Typography variant="h6">Welcome to FastGPT</Typography>
        <FormControlLabel control={
          <Switch checked={testInput} onChange={handleTestInputChange} name="darkMode"/>
        }
                          label={"Test Input"}/>

        <ModelSelector selectedModel={selectedModel} setSelectedModel={setSelectedModel}/>
      </Box>
      <Box sx={{
        display: 'flex',
        flexGrow: 1,
        mb: 2,
        overflow: 'hidden'
      }}>
        <ChatOutput outputText={outputText} outputContainerRef={outputContainerRef}/>
        <ChatOutput outputText={outputCodeText} outputContainerRef={outputCodeContainerRef}/>
      </Box>
      <ChatPrompt
        outputText={outputText} setOutputText={setOutputText}
        setOutputCodeText={setOutputCodeText}
        websocketRef={websocketRef}
        connectWebsocket={connectWebsocket}
        selectedModel={selectedModel}
        testInput={testInput}
      />
    </Box>
  );
}

export default FastGPTChat;