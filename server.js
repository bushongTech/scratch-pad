import Docker from 'dockerode';
import express from 'express';

const docker = new Docker({ socketPath: '/var/run/docker.sock' });
const app = express();
const PORT = 8503; // Private port for Apollo-Mission-Control

app.get('/api/microservices', async (req, res) => {
  try {
    const containers = await docker.listContainers();

    const services = containers
      .map(container => {
        const name = container.Names[0].replace('/', '');

        // Exclude Apollo-Mission-Control itself and containers with 'lavin' in the name
        if (name.includes('apollo-mission-control') || /lavin/i.test(name)) return null;

        // Get first available public TCP port that's not 8503
        const frontendPort = container.Ports.find(
          p => p.Type === 'tcp' && p.PublicPort && p.PublicPort !== PORT
        );

        if (!frontendPort) return null;

        return {
          title: name,
          dockerPublicPort: frontendPort.PublicPort,
        };
      })
      .filter(Boolean); // Remove null values

    res.json(services);
  } catch (error) {
    console.error('Error retrieving Docker containers:', error.message);
    res.status(500).json({ error: 'Unable to fetch microservices' });
  }
});

app.listen(PORT, () => {
  console.log(`Apollo-Mission-Control is running on port ${PORT}`);
});