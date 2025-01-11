import React, { useState } from 'react';
import { Box, TextField, Button, Paper } from '@mui/material';
import axios from 'axios';

export const HubspotContactsForm = ({ user, org }) => {
  const [contactId, setContactId] = useState('');
  const [properties, setProperties] = useState('');
  const [result, setResult] = useState(null);

  // Helper function to build FormData with user/org
  const buildFormData = (extraFields = {}) => {
    const formData = new FormData();
    formData.append('user_id', user);
    formData.append('org_id', org);
    Object.entries(extraFields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    return formData;
  };

  const handleGetContact = async () => {
    try {
      const formData = buildFormData({ contact_id: contactId });
      const response = await axios.post(
        'http://localhost:8000/integrations/hubspot/contact/get',
        formData
      );
      setResult(response.data);
    } catch (err) {
      alert(err?.response?.data?.detail || err.message);
    }
  };

  const handleCreateContact = async () => {
    try {
      const formData = buildFormData({ properties_str: properties });
      const response = await axios.post(
        'http://localhost:8000/integrations/hubspot/contact/create',
        formData
      );
      setResult(response.data);
    } catch (err) {
      alert(err?.response?.data?.detail || err.message);
    }
  };

  const handleUpdateContact = async () => {
    try {
      const formData = buildFormData({
        contact_id: contactId,
        properties_str: properties,
      });
      const response = await axios.post(
        'http://localhost:8000/integrations/hubspot/contact/update',
        formData
      );
      setResult(response.data);
    } catch (err) {
      alert(err?.response?.data?.detail || err.message);
    }
  };

  const handleDeleteContact = async () => {
    try {
      const formData = buildFormData({ contact_id: contactId });
      const response = await axios.post(
        'http://localhost:8000/integrations/hubspot/contact/delete',
        formData
      );
      setResult(response.data);
    } catch (err) {
      alert(err?.response?.data?.detail || err.message);
    }
  };

  const handleClearFields = () => {
    setContactId('');
    setProperties('');
    setResult(null);
  };

  return (
    <Box display="flex" flexDirection="column" width="100%" gap={2} sx={{ mt: 3 }}>
      <TextField
        label="Contact ID"
        variant="outlined"
        value={contactId}
        onChange={e => setContactId(e.target.value)}
        helperText="For get, update, delete operations"
      />

      <TextField
        label="Contact Properties (JSON)"
        variant="outlined"
        multiline
        rows={4}
        value={properties}
        onChange={e => setProperties(e.target.value)}
        helperText='Example: {"email":"test@hubspot.com","firstname":"Test","lastname":"User"}'
      />

      <Box display="flex" gap={2} flexWrap="wrap">
        <Button variant="contained" onClick={handleGetContact}>
          Get Contact
        </Button>
        <Button variant="contained" onClick={handleCreateContact}>
          Create Contact
        </Button>
        <Button variant="contained" onClick={handleUpdateContact}>
          Update Contact
        </Button>
        <Button variant="contained" color="error" onClick={handleDeleteContact}>
          Delete Contact
        </Button>
      </Box>

        <Button variant="outlined" onClick={handleClearFields}>
            Clear Fields
        </Button>

        <Box>
        <Paper
          variant="outlined"
          sx={{
            mt: 2,
            p: 2,
            width: '600px',
            minHeight: '200px',
            maxHeight: '400px',
            overflow: 'auto',
          }}
        >
          <Box component="pre" fontFamily="monospace" margin={0}>
            {result 
              ? JSON.stringify(result, null, 2)
              : 'No result yet.'
            }
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};
