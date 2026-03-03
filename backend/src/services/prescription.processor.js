import Prescription from '../models/prescription.model.js';
import logger from '../utils/logger.js';
import fs from 'fs';
import FormData from 'form-data';
import axios from 'axios';
import path from 'path';

/**
 * Asynchronous Background Processor
 * This simulates a worker queue job. It should NOT be awaited by the controller.
 */
export const processPrescriptionAsync = async (prescriptionId) => {
    try {
        // 1. Fetch prescription and mark as processing
        const prescription = await Prescription.findById(prescriptionId);
        if (!prescription) {
            logger.error(`Processor Error: Prescription ${prescriptionId} not found`);
            return;
        }

        prescription.status = 'processing';
        await prescription.save();
        logger.info(`Started processing prescription ${prescriptionId}`);

        // 2. Transmit image blob to ML API physically bypassing fake processors
        const formData = new FormData();
        const absoluteImagePath = path.resolve(prescription.imagePath);
        formData.append('file', fs.createReadStream(absoluteImagePath));

        logger.info(`Sending image to Python ML Engine: ${absoluteImagePath}`);
        const mlResponse = await axios.post('http://127.0.0.1:5000/process/image', formData, {
            headers: {
                ...formData.getHeaders()
            },
            maxBodyLength: 104857600
        });

        const result = mlResponse.data;
        if (result.status !== 'success' && result.status !== 'analyzed' && result.status !== 'operational') {
            throw new Error(result.error || 'ML pipeline returned unstable validation format.');
        }

        const extractedDrugs = result.medicines || [];
        const interactionWarnings = result.interactions || [];
        const warningsList = result.warnings || [];

        // Construct total risk
        const totalRisk = interactionWarnings.reduce((sum, int) => sum + (int.risk_score || 0), 0);
        const riskScore = Math.min(Math.round(totalRisk * 100), 100);

        const fhirPayload = {
            message: "FastAPI Analysis Map",
            pipeline_time: result.processing_time_ms,
            warnings: warningsList
        };

        // 4. Update Database
        prescription.extractedDrugs = extractedDrugs;
        prescription.interactionWarnings = interactionWarnings;
        prescription.riskScore = riskScore;
        prescription.fhir = fhirPayload;
        prescription.status = 'analyzed';

        await prescription.save();
        logger.info(`Successfully analyzed prescription ${prescriptionId}`);

    } catch (error) {
        logger.error(`Failed to process prescription ${prescriptionId}: ${error.message}`);

        // Ensure failed state is recorded
        await Prescription.findByIdAndUpdate(prescriptionId, {
            status: 'failed',
            errorMessage: error.message || 'Unknown processing error occurred',
        });
    }
};
