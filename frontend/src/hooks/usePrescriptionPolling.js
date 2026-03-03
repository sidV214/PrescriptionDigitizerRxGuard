import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api.js';
import { ROUTES } from '../constants/routes.js';

export const usePrescriptionPolling = (prescriptionId) => {
    const [status, setStatus] = useState('uploaded');
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        console.log('[POLLING] Effect started with ID:', prescriptionId);
        if (!prescriptionId) return;

        let timeoutId;

        const pollStatus = async () => {
            console.log('[POLLING] Requesting status for:', prescriptionId);
            try {
                const data = await api.getPrescriptionStatus(prescriptionId);
                console.log('[POLLING] Response data:', data);
                setStatus(data.status);

                if (data.status === 'analyzed') {
                    console.log('[POLLING] Status analyzed! Executing navigate()');
                    navigate(ROUTES.PHARMACIST.SAFETY_REPORT.replace(':id', prescriptionId));
                    return; // Stop polling
                }

                if (data.status === 'failed' || data.status === 'error') {
                    console.log('[POLLING] Error identified by backend status.');
                    setError(data.errorMessage || 'Prescription analysis failed.');
                    return; // Stop polling
                }

                console.log('[POLLING] Scheduling next poll iteration.');
                timeoutId = setTimeout(pollStatus, 3000);
            } catch (err) {
                console.error('[POLLING] Polling loop caught error:', err);
                setError('Connection lost while checking status. Please try again.');
            }
        };

        // Start polling loop
        pollStatus();

        return () => {
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [prescriptionId, navigate]);

    return { status, error };
};
