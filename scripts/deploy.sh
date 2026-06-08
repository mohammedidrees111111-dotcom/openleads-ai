#!/bin/bash
set -e

echo "=========================================="
echo "  OpenLeads AI - Deployment Script"
echo "  Built by Mohammed Idrees"
echo "=========================================="

case "${1:-help}" in
  local)
    echo "Starting local development environment..."
    docker-compose up --build -d
    echo "✅ Backend: http://localhost:8000"
    echo "✅ Frontend: http://localhost:3000"
    echo "✅ Docs: http://localhost:8000/docs"
    ;;

  stop)
    echo "Stopping all services..."
    docker-compose down
    echo "✅ All services stopped"
    ;;

  logs)
    docker-compose logs -f "${2:-}"
    ;;

  migrate)
    echo "Running database migrations..."
    docker-compose exec backend alembic upgrade head
    echo "✅ Migrations complete"
    ;;

  seed)
    echo "Seeding demo data..."
    docker-compose exec backend python scripts/seed.py
    echo "✅ Demo data seeded"
    ;;

  test)
    echo "Running tests..."
    docker-compose exec backend pytest
    docker-compose exec frontend npm test
    echo "✅ Tests complete"
    ;;

  clean)
    echo "Cleaning up..."
    docker-compose down -v
    docker system prune -f
    echo "✅ Cleanup complete"
    ;;

  backup)
    echo "Backing up database..."
    docker-compose exec postgres pg_dump -U postgres openleads > backup_$(date +%Y%m%d_%H%M%S).sql
    echo "✅ Database backed up"
    ;;

  deploy:railway)
    echo "Deploying to Railway..."
    railway up
    echo "✅ Deployed to Railway"
    ;;

  deploy:render)
    echo "Deploying to Render..."
    render deploy
    echo "✅ Deployed to Render"
    ;;

  *)
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  local           Start local development environment"
    echo "  stop            Stop all services"
    echo "  logs [service]  View logs"
    echo "  migrate         Run database migrations"
    echo "  seed            Seed demo data"
    echo "  test            Run tests"
    echo "  clean           Clean up all data"
    echo "  backup          Backup database"
    echo "  deploy:railway  Deploy to Railway"
    echo "  deploy:render   Deploy to Render"
    ;;
esac
