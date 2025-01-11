// hubspot.js
import { useState, useEffect } from 'react';
import { Box, Button, CircularProgress } from '@mui/material';
import axios from 'axios';

export const HubspotIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    useEffect(() => {
        // If credentials exist in integrationParams, we consider it "connected"
        setIsConnected(Boolean(integrationParams?.credentials));
    }, [integrationParams]);

    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const formData = new FormData();
            formData.append("user_id", user);
            formData.append("org_id", org);

            // Request the OAuth Authorization URL
            const response = await axios.post(
                "http://localhost:8000/integrations/hubspot/authorize",
                formData
            );
            const authURL = response?.data;
            if (!authURL) {
                throw new Error("No authorization URL returned from server.");
            }

            // Open OAuth flow in a new window
            const newWindow = window.open(authURL, "HubSpot Authorization", "width=600, height=600");

            // Poll for the window to close
            const pollTimer = setInterval(() => {
                if (!newWindow || newWindow.closed) {
                    clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 300);
        } catch (e) {
            console.error(e);
            setIsConnecting(false);
            alert(e?.response?.data?.detail || e.message);
        }
    };

    const handleWindowClosed = async () => {
        // Attempt to retrieve credentials from the server
        try {
            const formData = new FormData();
            formData.append("user_id", user);
            formData.append("org_id", org);

            const response = await axios.post(
                "http://localhost:8000/integrations/hubspot/credentials",
                formData
            );
            const creds = response.data;
            if (creds) {
                setIsConnecting(false);
                setIsConnected(true);
                setIntegrationParams(prev => ({
                    ...prev,
                    credentials: creds,
                    type: "Hubspot"
                }));
            }
        } catch (e) {
            console.error(e);
            setIsConnecting(false);
            alert(e?.response?.data?.detail || e.message);
        }
    };

    return (
        <Box sx={{ mt: 2 }}>
            <Box
                display="flex"
                alignItems="center"
                justifyContent="center"
                sx={{ mt: 2 }}
            >
                <Button
                    variant="contained"
                    onClick={isConnected ? undefined : handleConnectClick}
                    color={isConnected ? "success" : "primary"}
                    disabled={isConnecting}
                    style={{
                        pointerEvents: isConnected ? "none" : "auto",
                        cursor: isConnected ? "default" : "pointer",
                        opacity: isConnected ? 1 : undefined
                    }}
                >
                    {isConnected
                        ? "HubSpot Connected"
                        : isConnecting
                            ? <CircularProgress size={20} />
                            : "Connect to HubSpot"
                    }
                </Button>
            </Box>
        </Box>
    );
};
