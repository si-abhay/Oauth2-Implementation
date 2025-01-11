import { useState } from "react";
import { Box, Autocomplete, TextField } from "@mui/material";
import { AirtableIntegration } from "./integrations/airtable";
import { NotionIntegration } from "./integrations/notion";
import { HubspotIntegration } from "./integrations/hubspot";

import { DataForm } from "./data-form";
import { HubspotContactsForm } from "./contact-form";

const integrationMapping = {
  Notion: NotionIntegration,
  Airtable: AirtableIntegration,
  Hubspot: HubspotIntegration,
};

export const IntegrationForm = () => {
  const [integrationParams, setIntegrationParams] = useState({});
  const [user, setUser] = useState("TestUser");
  const [org, setOrg] = useState("TestOrg");
  const [currType, setCurrType] = useState(null);

  const CurrentIntegration = currType ? integrationMapping[currType] : null;

  return (
    <Box display="flex" flexDirection="column" width="100%" alignItems="center">
      {/* Basic fields for user/org/integration type */}
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

      {/* Render the specific integration's "connect" component if chosen */}
      {CurrentIntegration && (
        <Box sx={{ mt: 2 }}>
          <CurrentIntegration
            user={user}
            org={org}
            integrationParams={integrationParams}
            setIntegrationParams={setIntegrationParams}
          />
        </Box>
      )}

      {integrationParams?.credentials &&
       integrationParams?.type !== "Hubspot" && (
         <Box sx={{ mt: 2 }}>
           <DataForm
             integrationType={integrationParams?.type}
             credentials={integrationParams?.credentials}
           />
         </Box>
      )}

      {/* 
        If we have credentials and the type is HubSpot, 
        show DataForm and ContactsForm side by side 
      */}
      {integrationParams?.credentials && integrationParams?.type === "Hubspot" && (
        <Box
          sx={{
            mt: 4,
            display: "flex",
            flexDirection: "row",
            gap: 4,
            justifyContent: "center",
            width: "100%",
            flexWrap: "wrap",
          }}
        >

          <Box>
            <DataForm
              integrationType={integrationParams?.type}
              credentials={integrationParams?.credentials}
            />
          </Box>

          <Box>
            <HubspotContactsForm
              user={integrationParams.credentials.user_id || user}
              org={integrationParams.credentials.org_id || org}
            />
          </Box>
        </Box>
      )}
    </Box>
  );
};
