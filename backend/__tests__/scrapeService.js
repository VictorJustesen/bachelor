const axios = require('axios');
const { getBuildingInfo } = require('../services/scrapeService');

jest.mock('axios');

describe('scrapeService', () => {
  describe('getBuildingInfo', () => {
    it('should return data from the scraper service on success', async () => {
      const mockReq = { body: { address: 'Test Address 123' } };
      const mockRes = { json: jest.fn() };
      const apiResponse = { data: { address: 'Test Address 123', sqm: 100 } };

      axios.post.mockResolvedValue(apiResponse);

      await getBuildingInfo(mockReq, mockRes);

      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/scrape/building-info'),
        mockReq.body,
        expect.any(Object)
      );
      expect(mockRes.json).toHaveBeenCalledWith(apiResponse.data);
    });

    it('should return fallback mock data on scraper service failure', async () => {
      const mockReq = { body: { address: 'Test Address 123' } };
      const mockRes = { json: jest.fn() };

      axios.post.mockRejectedValue(new Error('Network Error'));

      await getBuildingInfo(mockReq, mockRes);

      expect(mockRes.json).toHaveBeenCalled();
      const response = mockRes.json.mock.calls[0][0];
      expect(response).toHaveProperty('source', 'fallback_mock');
      expect(response).toHaveProperty('address', 'Test Address 123');
    });
  });
});