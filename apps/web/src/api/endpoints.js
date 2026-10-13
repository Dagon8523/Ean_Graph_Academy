import { request } from './client.js';
export const learningPath = (body, signal) => request('POST', '/v1/recommendations/learning-path', { body, signal });
export const health = signal => request('GET', '/health', { signal });

export const conversationMessage = body => request('POST', '/v1/conversations/message', { body });
export const deleteConversation = id => request('DELETE', `/v1/conversations/${id}`);
