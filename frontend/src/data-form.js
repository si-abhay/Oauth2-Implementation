// data-form.js
import { useState } from "react";
import { Box, Button, Paper } from "@mui/material";
import axios from "axios";

const endpointMapping = {
    Notion: "notion",
    Airtable: "airtable",
    Hubspot: "hubspot",
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];
  
    const handleLoad = async () => {
      if (!credentials?.user_id || !credentials?.org_id) {
        alert('user_id or org_id missing!');
        return;
      }
      try {
        const formData = new FormData();
        // Only passing the user_id, org_id, so the backend can handle refresh
        const minimalPayload = {
          user_id: credentials.user_id,
          org_id: credentials.org_id,
        };
        formData.append("credentials", JSON.stringify(minimalPayload));
  
        const response = await axios.post(
          `http://localhost:8000/integrations/${endpoint}/load`,
          formData
        );
        setLoadedData(response.data);
      } catch (err) {
        alert(err?.response?.data?.detail || err.message);
      }
    };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      flexDirection="column"
      width="100%"
    >
      <Box display="flex" flexDirection="column" width="100%">
        
        {/* A Paper to display the loaded data in a big area */}
        <Paper
          variant="outlined"
          sx={{
            mt: 2,
            p: 2,
            width: '600px',       // Make the data area wider
            minHeight: '200px',   
            maxHeight: '400px',   // Limit how tall it can grow
            overflow: 'auto',     // Scroll if content is too large
          }}
        >
          <Box component="pre" fontFamily="monospace" margin={0}>
            {loadedData 
              ? JSON.stringify(loadedData, null, 2)
              : 'No data yet.'
            }
          </Box>
        </Paper>

      </Box>
      <Button 
        onClick={handleLoad}
        sx={{ mt: 2 }}
        variant="contained"
      >
        Load Data
      </Button>
      <Button
        onClick={() => setLoadedData(null)}
        sx={{ mt: 1 }}
        variant="contained"
      >
        Clear Data
      </Button>
    </Box>
  );
};