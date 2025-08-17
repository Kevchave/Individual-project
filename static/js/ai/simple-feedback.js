// Simple AI Feedback System using Gemini API
// Provides one positive note and one improvement note based on metrics and goals

class SimpleAIFeedback {
    constructor(apiKey = null) {
        this.apiKey = apiKey;
        this.apiEndpoint = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent';
        this.model = 'gemini-1.5-flash';
    }

    async generateFeedback(sessionData, sessionMetrics, userGoals, isRecentSession = true) {
        try {
            const prompt = this.buildPrompt(sessionData, sessionMetrics, userGoals, isRecentSession);
            const response = await this.callAI(prompt);
            return this.parseResponse(response);
        } catch (error) {
            console.error('AI feedback error:', error);
            throw error; // Let dashboard handle the error
        }
    }

    buildPrompt(sessionData, sessionMetrics, userGoals, isRecentSession) {
        const stats = sessionMetrics?.stats || {};
        const metricsData = sessionMetrics?.metrics || [];
        
        let prompt = `You are a speech coach providing concise feedback. 

        Session Data:
        - Duration: ${sessionData.duration_seconds || 0} seconds
        - Average WPM: ${stats.avg_wpm || 0} (words per minute - speaking speed)
        - Average Volume: ${stats.avg_volume || 0} dB (audio loudness - higher is louder)
        - Average Pitch: ${stats.avg_pitch || 0} Hz (voice frequency - typically 85-255 Hz for adults)
        - Average Confidence: ${stats.avg_confidence || 0} (transcription accuracy 0-1, NOT speaker confidence - higher means clearer speech/audio)
        - Average Silence Ratio: ${stats.avg_silence_ratio || 0} (proportion of silence vs speech, 0-1 scale)

        User Goals:
        - WPM Target: ${userGoals?.target_wpm || 'Not set'}
        - Volume Target: ${userGoals?.target_volume || 'Not set'}
        - Pitch Target: ${userGoals?.target_pitch || 'Not set'}`;

        if (!isRecentSession && metricsData.length > 0) {
            prompt += `

        Historical Data (${metricsData.length} sessions):
        ${this.formatHistoricalData(metricsData)}`;
        }

        prompt += `

        IMPORTANT CONTEXT:
        - "Confidence" refers to how well the speech recognition system understood the audio (audio quality, speech clarity), NOT the speaker's self-confidence
        - "Silence Ratio" measures pauses and gaps in speech (lower is more continuous speaking)
        - Focus on actionable, specific feedback based on the metrics provided

        Respond ONLY with valid JSON in this exact format. Do not include any other text, explanations, or markdown formatting:

        {
            "positive_note": "One specific thing they're doing well",
            "improvement_note": "One specific area to focus on improving"
        }

        The response must be valid JSON that can be parsed directly. Focus on the most impactful metric. Be specific and actionable.`;

        return prompt;
    }

    formatHistoricalData(metrics) {
        // Group metrics by session for better AI analysis
        const sessions = [];
        
        metrics.forEach((metric, index) => {
            sessions.push({
                session: index + 1,
                wpm: metric.wpm || 0,
                volume: metric.volume || 0,
                pitch: metric.pitch || 0,
                confidence: metric.confidence_score || 0,
                silence_ratio: metric.silence_ratio || 0
            });
        });

        return `Historical Session Metrics (Confidence = transcription accuracy, not speaker confidence):
${sessions.map(s => `Session ${s.session}: WPM=${s.wpm}, Volume=${s.volume}dB, Pitch=${s.pitch}Hz, Transcription_Accuracy=${s.confidence}, Silence_Ratio=${s.silence_ratio}`).join('\n')}

Analyze the trends across these sessions and provide insights on progress.`;
    }



    async callAI(prompt) {
        if (!this.apiKey) {
            throw new Error('API key not configured');
        }
    
        console.log('Making Gemini API call with model:', this.model);
    
        const response = await fetch(`${this.apiEndpoint}?key=${this.apiKey}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{
                        text: prompt
                    }]
                }],
                generationConfig: {
                    temperature: 0.7,
                    maxOutputTokens: 300,
                }
            })
        });
    
        console.log('Gemini API response status:', response.status);
    
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Gemini API error details:', errorText);
            throw new Error(`API call failed: ${response.status} - ${errorText}`);
        }
    
        const data = await response.json();
        
        if (data.candidates && data.candidates[0] && data.candidates[0].content) {
            return data.candidates[0].content.parts[0].text;
        } else {
            throw new Error('Invalid response format from Gemini API');
        }
    }
    parseResponse(aiResponse) {
        console.log('Raw Gemini response:', aiResponse); // Debug: see what we're getting
        
        try {
            // Clean the response - remove any markdown formatting or extra text
            let cleanResponse = aiResponse.trim();
            
            // Remove markdown code blocks if present
            cleanResponse = cleanResponse.replace(/```json\n?/g, '').replace(/```\n?/g, '');
            
            // Try to extract JSON if there's other text
            const jsonMatch = cleanResponse.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                cleanResponse = jsonMatch[0];
            }
            
            const feedback = JSON.parse(cleanResponse);
            
            return {
                success: true,
                feedback: {
                    positive_note: feedback.positive_note || 'Good session overall.',
                    improvement_note: feedback.improvement_note || 'Keep practicing regularly.'
                }
            };
        } catch (error) {
            console.warn('Failed to parse Gemini response as JSON:', aiResponse);
            console.warn('Parse error:', error);
            
            // Fallback: extract meaningful content even if not perfect JSON
            const fallbackFeedback = this.extractFallbackFeedback(aiResponse);
            return {
                success: true,
                feedback: fallbackFeedback
            };
        }
    }
    
    // Add this new method to handle cases where JSON parsing fails
    extractFallbackFeedback(response) {
        // Basic fallback if JSON parsing fails
        const lines = response.split('\n').filter(line => line.trim());
        
        let positive_note = 'Good session overall.';
        let improvement_note = 'Keep practicing regularly.';
        
        // Try to find positive and improvement content
        for (const line of lines) {
            if (line.toLowerCase().includes('positive') || line.toLowerCase().includes('good') || line.toLowerCase().includes('well')) {
                positive_note = line.replace(/['"]/g, '').trim();
            }
            if (line.toLowerCase().includes('improve') || line.toLowerCase().includes('focus') || line.toLowerCase().includes('try')) {
                improvement_note = line.replace(/['"]/g, '').trim();
            }
        }
        
        return { positive_note, improvement_note };
    }

    setApiKey(apiKey) {
        this.apiKey = apiKey;
    }

    isConfigured() {
        return !!this.apiKey;
    }
}

// Create global instance
export const simpleAIFeedback = new SimpleAIFeedback();

// Convenience function
export async function generateSimpleFeedback(sessionData, sessionMetrics, userGoals, isRecentSession = true) {
    return await simpleAIFeedback.generateFeedback(sessionData, sessionMetrics, userGoals, isRecentSession);
} 