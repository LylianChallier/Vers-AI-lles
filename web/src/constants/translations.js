import { minutesToHHMM, inMinutes } from '../utils/time'

export const HOURS = {
  chateau: { open: '09:00', close: '18:30', last: '17:45' },
  trianon: { open: '12:00', close: '18:30', last: '17:45' },
}

export const LANG_HINTS = {
  fr: 'Réponds en français clair et chaleureux.',
  en: 'Respond in English with concise sentences.',
}

export const SUGGESTION_KEYS = [
  'avoidQueues',
  'hallMirrors',
  'familyFriendly',
  'wheelchair',
  'food',
  'halfDay',
]

export const TRANSLATIONS = {
  en: {
    initialAssistant:
      'Welcome! I’m your Versailles Concierge. Share your timing, preferences, or constraints and I’ll craft a tailored plan for your visit.',
    app: {
      title: 'Versailles Concierge',
      subtitle: 'Chat + Map assistant for the Château & Gardens',
    },
    crowd: {
      title: 'Crowd now',
      labels: { low: 'Low', rising: 'Rising', peak: 'Peak', busy: 'Busy' },
      tip: 'Tip: Peak 11:00–15:00. Hall of Mirrors calmer after 15:00.',
    },
    hours: {
      title: "Today’s key hours",
      chateau: 'Château',
      trianon: 'Trianon',
      lastEntry: 'Last entry',
      entryInfo: (open) =>
        `If you hold a ${open} ticket, you must enter by ${minutesToHHMM(inMinutes(open) + 30)} (30-minute window).`,
      entryLate: 'Last admission has passed for today.',
    },
    weather: {
      title: 'Weather-aware tip',
      loading: 'Loading weather advice…',
      error: 'Weather fetch failed',
      fallbackLabel: 'Temporary tip',
    },
    mapCard: {
      title: 'Map & Route',
      hide: 'Hide',
      controls: {
        originPlaceholder: 'Origin (e.g., Rive Gauche Station)',
        destinationPlaceholder: 'Destination',
        profile: { walking: 'Walking', driving: 'Driving', cycling: 'Cycling' },
      },
      buttons: {
        versaillesFromOrigin: 'To Château from Origin',
        routeAB: 'Route A → B',
        multiDemo: 'Multi-stop (demo)',
        askConcierge: 'Ask Concierge',
      },
      prompts: {
        ask: (origin, destination) =>
          `Start at: ${origin}. Destination: ${destination}. Suggest a timed visit plan with weather-aware tips.`,
      },
      directionsTitle: 'Directions',
      loading: 'Computing route…',
      error: 'Route failed',
    },
    plan: {
      title: 'Suggested plan',
      openMap: 'Open Map',
      closeMap: 'Close Map',
      empty: 'Send a request to the concierge to generate a plan.',
      locationButton: {
        request: 'Use my location',
        loading: 'Locating…',
        refresh: 'Update my location',
      },
      locationPrompt: 'Allow location so the concierge can tailor routes and timing tips.',
      locationShared: ({ lat, lon, accuracy }) =>
        `Location shared (${lat}, ${lon}${accuracy ? ` ±${accuracy} m` : ''}).`,
      locationHint: ({ lat, lon, accuracy }) =>
        `My current position: latitude ${lat}, longitude ${lon}${accuracy ? ` (±${accuracy} m)` : ''}.`,
      locationErrors: {
        unsupported: 'Geolocation is not available in this browser.',
        permission: 'Location permission denied. You can retry from your browser settings.',
        unavailable: 'Unable to retrieve your position right now.',
        timeout: 'Location timed out. Try again near a window or after checking your connection.',
        unknown: 'Something went wrong while locating you. Please try again shortly.',
      },
      youAreHere: 'You are here',
    },
    planActions: {
      buyTickets: 'Buy tickets',
      accessibility: 'Accessibility',
      languages: 'Languages',
    },
    suggestionsTitle: 'Smart suggestions',
    suggestions: {
      avoidQueues: 'Avoid queues',
      hallMirrors: 'Best time for Hall of Mirrors',
      familyFriendly: 'Family-friendly route',
      wheelchair: 'Need wheelchair tips',
      food: 'Where to eat?',
      halfDay: 'Half-day itinerary',
    },
    chat: {
      title: 'Chat with your Concierge',
      status: 'Online',
      clear: 'Clear chat',
      placeholder: 'Ask for a plan, a time slot, or tips…',
      sendIdle: 'Send',
      sendLoading: 'Sending…',
      assistantLoading: 'The concierge is preparing a response…',
      errorGeneral:
        'The concierge is having an issue. Make sure the backend (port 8002) is running or try again shortly.',
      errorDetailsPrefix: 'Technical details:',
    },
    route: {
      summary: (km, minutes, profile) => `📍 Itinerary ≈ ${km.toFixed(1)} km · ≈ ${minutes} min (${profile})`,
    },
    compassLabel: 'Open concierge map',
    footer:
      'Inspired by Versailles’ gilded halls & geometric gardens • Swap mock data for live APIs when ready',
  },
  fr: {
    initialAssistant:
      'Bienvenue ! Je suis votre concierge de Versailles. Indiquez vos horaires, préférences ou contraintes et je préparerai un plan sur mesure pour votre visite.',
    app: {
      title: 'Concierge Versailles',
      subtitle: 'Assistant Chat + Carte pour le château et les jardins',
    },
    crowd: {
      title: 'Affluence actuelle',
      labels: { low: 'Faible', rising: 'En hausse', peak: 'Pic', busy: 'Chargé' },
      tip: 'Astuce : pic 11h00–15h00. Galerie des Glaces plus calme après 15h00.',
    },
    hours: {
      title: 'Horaires du jour',
      chateau: 'Château',
      trianon: 'Trianon',
      lastEntry: 'Dernière entrée',
      entryInfo: (open) =>
        `Avec un billet ${open}, l’accès est garanti jusqu’à ${minutesToHHMM(inMinutes(open) + 30)} (créneau de 30 min).`,
      entryLate: 'La dernière admission est passée pour aujourd’hui.',
    },
    weather: {
      title: 'Conseil météo',
      loading: 'Chargement des conseils météo…',
      error: 'La récupération des informations météo a échoué',
      fallbackLabel: 'Astuce temporaire',
    },
    mapCard: {
      title: 'Carte & itinéraire',
      hide: 'Masquer',
      controls: {
        originPlaceholder: 'Origine (ex : Gare Rive Gauche)',
        destinationPlaceholder: 'Destination',
        profile: { walking: 'Marche', driving: 'Voiture', cycling: 'Vélo' },
      },
      buttons: {
        versaillesFromOrigin: 'Vers le château depuis l’origine',
        routeAB: 'Itinéraire A → B',
        multiDemo: 'Multi-étapes (démo)',
        askConcierge: 'Demander au concierge',
      },
      prompts: {
        ask: (origin, destination) =>
          `Point de départ : ${origin}. Destination : ${destination}. Propose un itinéraire de visite avec horaires optimisés et conseils météo.`,
      },
      directionsTitle: 'Étapes clés',
      loading: 'Calcul de l’itinéraire…',
      error: 'Itinéraire indisponible',
    },
    plan: {
      title: 'Plan suggéré',
      openMap: 'Afficher la carte',
      closeMap: 'Fermer la carte',
      empty: 'Envoyez une demande au concierge pour générer un plan.',
      locationButton: {
        request: 'Utiliser ma position',
        loading: 'Localisation…',
        refresh: 'Actualiser ma position',
      },
      locationPrompt: 'Autorisez la localisation pour adapter trajets et conseils horaires.',
      locationShared: ({ lat, lon, accuracy }) =>
        `Position partagée (${lat}, ${lon}${accuracy ? ` ±${accuracy} m` : ''}).`,
      locationHint: ({ lat, lon, accuracy }) =>
        `Ma position actuelle : latitude ${lat}, longitude ${lon}${accuracy ? ` (±${accuracy} m)` : ''}.`,
      locationErrors: {
        unsupported: 'La géolocalisation n’est pas disponible sur ce navigateur.',
        permission:
          'Autorisation de localisation refusée. Vous pouvez réessayer depuis les réglages du navigateur.',
        unavailable: 'Impossible de récupérer votre position pour le moment.',
        timeout: 'La localisation a expiré. Réessayez près d’une fenêtre ou après vérification de la connexion.',
        unknown: 'Un imprévu a empêché la localisation. Merci de réessayer sous peu.',
      },
      youAreHere: 'Vous êtes ici',
    },
    planActions: {
      buyTickets: 'Billets',
      accessibility: 'Accessibilité',
      languages: 'Langues',
    },
    suggestionsTitle: 'Suggestions rapides',
    suggestions: {
      avoidQueues: 'Éviter les files',
      hallMirrors: 'Moment idéal pour la Galerie des Glaces',
      familyFriendly: 'Parcours famille',
      wheelchair: 'Conseils accessibilité',
      food: 'Où manger ?',
      halfDay: 'Itinéraire 3 h',
    },
    chat: {
      title: 'Discutez avec votre concierge',
      status: 'En ligne',
      clear: 'Effacer',
      placeholder: 'Demandez un plan, un créneau ou un conseil…',
      sendIdle: 'Envoyer',
      sendLoading: 'Envoi…',
      assistantLoading: 'Le concierge prépare sa réponse…',
      errorGeneral:
        'Le concierge rencontre un imprévu. Assurez-vous que le backend (port 8002) est lancé ou réessayez bientôt.',
      errorDetailsPrefix: 'Détails techniques :',
    },
    route: {
      summary: (km, minutes, profile) => `📍 Itinéraire ≈ ${km.toFixed(1)} km · ≈ ${minutes} min (${profile})`,
    },
    compassLabel: 'Ouvrir la carte du concierge',
    footer:
      'Inspiré par les ors et jardins de Versailles • Remplacez les données mock par des API live quand vous voulez',
  },
}

export const WEATHER_FALLBACK = {
  en: {
    condition: 'partly-cloudy',
    tempC: 22,
    advice: 'Sunny morning → start with the Gardens; Hall of Mirrors after 14:30 when tours thin out.',
  },
  fr: {
    condition: 'partly-cloudy',
    tempC: 22,
    advice: 'Matin ensoleillé → commencez par les jardins ; Galerie des Glaces plus calme après 15h.',
  },
}
