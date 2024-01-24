import React, {useState} from 'react';
import {ThemeProvider, createTheme} from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import {FormControlLabel} from "@mui/material";
import Switch from "@mui/material/Switch";  // renamed to MuiSwitch
import Box from "@mui/material/Box";
import FastGPTChat from "./components/FastGPTChat";


function App() {
  const [darkMode, setDarkMode] = useState(true);


  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
    },
  });

  const handleThemeChange = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline/>
      {/* Header with Dark Mode Toggle */}
      <Box sx={{
        display: 'flex', alignItems: 'center', justifyContent: 'flex-end', width:
          '100%', padding: 0
      }}>
        <FormControlLabel
          control={<Switch checked={darkMode} onChange={handleThemeChange} name="darkMode"/>}
          label={"Dark"}
        />
      </Box>
      <FastGPTChat/>
    </ThemeProvider>
  );
}

export default App;
