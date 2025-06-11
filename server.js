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
    const name = container.Names?.[0]?.replace('/', '');

    // Exclude Apollo-Mission-Control and anything with "lavin" in the name
    if (!name || name.includes('apollo-mission-control') || /lavin/i.test(name)) return null;

    const frontendPort = Array.isArray(container.Ports)
      ? container.Ports.find(p => p.Type === 'tcp' && p.PublicPort && p.PublicPort !== PORT)
      : null;

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


function prettifyTitle(slug) {
  return slug
    .split('-')
    .map(word => word.toUpperCase() === word ? word : word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

const services = containers
  .map(container => {
    const rawName = container.Names?.[0]?.replace('/', '');

    // Exclude Apollo, Lavin, Etcd, and Synnax
    if (
      !rawName ||
      rawName.includes('apollo-mission-control') ||
      /lavin|etcd|synnax/i.test(rawName)
    ) return null;

    const frontendPort = Array.isArray(container.Ports)
      ? container.Ports.find(p => p.Type === 'tcp' && p.PublicPort && p.PublicPort !== PORT)
      : null;

    if (!frontendPort) return null;

    return {
      title: prettifyTitle(rawName),
      dockerPublicPort: frontendPort.PublicPort,
    };
  })
  .filter(Boolean);
