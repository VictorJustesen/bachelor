const axios = require('axios');
const { getBuildingInfo } = require('../services/scrapeService');

jest.mock('axios');

describe('scrapeService', () => {
  const mockReq = { body: { address: 'Test Address 123' } };
  let mockRes;

  beforeEach(() => {
    mockRes = {
      json: jest.fn(),
    };
  });

  it('should return data when the scraper service succeeds', async () => {
    const apiResponse = { data: { address: 'Test Address 123', sqm: 100 } };
    axios.post.mockResolvedValue(apiResponse);

    await getBuildingInfo(mockReq, mockRes);

    expect(mockRes.json).toHaveBeenCalledWith(apiResponse.data);
  });

  it('should return fallback data when the scraper service fails', async () => {
    axios.post.mockRejectedValue(new Error('Network Error'));

    await getBuildingInfo(mockReq, mockRes);

    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({
        address: 'Test Address 123',
        source: 'fallback_mock',
      })
    );
  });
});