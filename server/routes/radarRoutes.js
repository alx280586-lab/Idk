import { Router } from 'express';

import { RADAR_PRODUCTS } from '../config.js';
import { buildRadarTimeline, getLegendForProduct } from '../services/nwsRadarService.js';

const router = Router();

router.get('/products', (_req, res) => {
  res.json({ products: RADAR_PRODUCTS });
});

router.get('/:product/frames', async (req, res, next) => {
  try {
    const { product } = req.params;
    const timeline = await buildRadarTimeline(product);
    res.json(timeline);
  } catch (error) {
    next(error);
  }
});

router.get('/:product/legend', (req, res) => {
  const { product } = req.params;
  const legend = getLegendForProduct(product);
  if (!legend) {
    return res.status(404).json({ message: 'Legend not found for product.' });
  }
  res.json(legend);
});

export default router;
