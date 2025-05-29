import axios from 'axios';

const API_URL = 'http://localhost:8000/analyze'; // Adjust the URL as needed

export const fetchAnalysis = async (analysisGoal, tables, executeQueries = true) => {
    try {
        const response = await axios.post(API_URL, {
            analysisGoal,
            tables,
            executeQueries
        });
        console.log('API response:', response.data); // Log the response data
        if (response.status !== 200) {
            throw new Error(`Error: ${response.status} - ${response.statusText}`);
        }
        // Check if the response contains an error message
        if (response.data.error) {
            throw new Error(`API Error: ${response.data.error}`);
        }
        // Check if the response contains a success message
        if (response.data.success) {
            console.log('Success:', response.data.success);
        }
        return response.data;
    } catch (error) {
        console.error('Error fetching analysis:', error);
        throw error;
    }
};