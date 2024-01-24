import React, {useState, useEffect} from 'react';
import {Select, MenuItem, FormControl, InputLabel} from '@mui/material';
import {API_CONFIG} from "../config";

const ModelSelector = ({selectedModel, setSelectedModel}) => {
  const [models, setModels] = useState([]);


  useEffect(() => {
    fetch(`${API_CONFIG.PROTOCOL}://${API_CONFIG.BASEURL}/gpt_models`)
      .then(response => response.json())
      .then(data => {
        if (data.hasOwnProperty('gpt_models')) {
          setModels(data.gpt_models);
          if (data.gpt_models.length > 0) {
            setSelectedModel(data.gpt_models[0]);
          }
        }
      })
      .catch(error => {
        console.error('Error fetching models:', error);
      });
  }, [setSelectedModel]);

  const handleModelChange = (event) => {
    setSelectedModel(event.target.value);
  };

  return (
    <FormControl>
      <InputLabel id="model-selector-label">Model</InputLabel>
      <Select
        labelId="model-selector-label"
        value={selectedModel}
        onChange={handleModelChange}
        displayEmpty
        sx={{height: 40}}
      >
        {models.length > 0 ? models.map((model) => (
          <MenuItem key={model} value={model}>{model}</MenuItem>
        )) : (
          [<MenuItem key="no-models" value={''}>No models available</MenuItem>]
        )
        }
      </Select>
    </FormControl>
  )
}

export default ModelSelector;