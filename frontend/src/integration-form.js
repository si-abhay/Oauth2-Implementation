// integration-form.js
import { useState } from "react";
import { Box, Autocomplete, TextField } from "@mui/material";
import { AirtableIntegration } from "./integrations/airtable";
import { NotionIntegration } from "./integrations/notion";
import { HubspotIntegration } from "./integrations/hubspot";
import { DataForm } from "./data-form";
import { HubspotContactsForm } from './contact-form';

const integrationMapping = {
    Notion: NotionIntegration,
    Airtable: AirtableIntegration,
    Hubspot: HubspotIntegration,
};

export const IntegrationForm = () => {
    const [integrationParams, setIntegrationParams] = useState({});
    // Default to test user/org for local dev, Struggling with JS TBH! :((
    const [user, setUser] = useState("TestUser");
    const [org, setOrg] = useState("TestOrg");
    const [currType, setCurrType] = useState(null);

    const CurrentIntegration = currType ? integrationMapping[currType] : null;

    return (
        <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            flexDirection="column"
            sx={{ width: "100%" }}
        >
            <Box display="flex" flexDirection="column">
                <TextField
                    label="User"
                    value={user}
                    onChange={(e) => setUser(e.target.value)}
                    sx={{ mt: 2 }}
                />
                <TextField
                    label="Organization"
                    value={org}
                    onChange={(e) => setOrg(e.target.value)}
                    sx={{ mt: 2 }}
                />
                <Autocomplete
                    id="integration-type"
                    options={Object.keys(integrationMapping)}
                    sx={{ width: 300, mt: 2 }}
                    renderInput={(params) => (
                        <TextField {...params} label="Integration Type" />
                    )}
                    onChange={(_event, value) => setCurrType(value)}
                />
            </Box>

            {/* Render the integration component if chosen */}
            {CurrentIntegration && (
                <Box>
                    <CurrentIntegration
                        user={user}
                        org={org}
                        integrationParams={integrationParams}
                        setIntegrationParams={setIntegrationParams}
                    />
                </Box>
            )}

            {/* If we have credentials, render the DataForm */}
            {integrationParams?.credentials && (
                <Box sx={{ mt: 2 }}>
                    <DataForm
                        integrationType={integrationParams?.type}
                        credentials={integrationParams?.credentials}
                    />
                </Box>
            )}

            {/* If we have credentials and the integration is Hubspot, render the HubspotContactsForm */}
            {integrationParams?.type === "Hubspot" && integrationParams?.credentials && (
            <Box sx={{ mt: 2 }}>
                <HubspotContactsForm
                user={integrationParams.credentials.user_id || user}
                org={integrationParams.credentials.org_id || org}
                />
            </Box>
            )}
        </Box>
    );
};
