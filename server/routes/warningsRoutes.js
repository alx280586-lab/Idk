import { Router } from 'express';

import { fetchActiveWarnings } from '../services/nwsWarningsService.js';

const router = Router();

router.get('/', async (req, res, next) => {
  try {
    const { status } = req.query;
    const data = await fetchActiveWarnings(status);
    res.json(data);
  } catch (error) {
    next(error);
  }
});

export default router;
