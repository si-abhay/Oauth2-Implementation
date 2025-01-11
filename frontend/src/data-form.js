// data-form.js
import { useState } from "react";
import { Box, TextField, Button } from "@mui/material";
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
        if (!credentials) {
            alert("No credentials available. Please connect first.");
            return;
        }

        try {
            const formData = new FormData();
            // We pass the entire credentials object as JSON, JSON is just the best! 🚀
            formData.append("credentials", JSON.stringify(credentials));

            const response = await axios.post(
                `http://localhost:8000/integrations/${endpoint}/load`,
                formData
            );
            setLoadedData(response.data);
        } catch (e) {
            console.error(e);
            alert(e?.response?.data?.detail || e.message);
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
                <TextField
                    label="Loaded Data"
                    value={loadedData ? JSON.stringify(loadedData, null, 2) : ""}
                    sx={{ mt: 2 }}
                    InputLabelProps={{ shrink: true }}
                    disabled
                    multiline
                    rows={10}
                />
                <Button onClick={handleLoad} sx={{ mt: 2 }} variant="contained">
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
        </Box>
    );
};
