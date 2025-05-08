# 20250311 Replit.com prompt
## Initial
A modularly designed app called "flyers" for ios and android with a fully decentralized backend written in Go. we own the domain flyers.lol. The purpose of the app is to distribute and subscribe to events. It is important that it is possible to create and join entirely private distribution networks. A flyer object is a picture (or a short video) with a date, description, tags, location text, coordinates, owner, interested users and unique id, optionally it has sound, or an action button (so it is possible to register, book a time slot, etc). Events do not need to have location and coordinates, but the interface colors the edges of the input box in a neon red color if they do. The distribution networks, aka groups, aka topics (in a pubsub sense) typically correspond to a geographic area, such as "copenhagen", but private groups can also correspond to topics such as "poetry".

The app has a Tinder-like GUI: Swipe left to dislike, swipe right to like, swipe up to like and add to calendar. swipe down to access moderation tools, where you can add a community node, modify tags and flag for being illegal. If a user likes an event, they add their username to the event record. Other users only pull updates to an event if they trust the editor, and verify the usernames in the event record with a signing method based on a known cryptographic key. 

The app uses IPFS for storing files (sound, picture, video). The app uses a decentralized distributed and sharded database to store events (orbitdb). The media files are stored in the database as ipfs links. The user bootstraps the libp2p pubsub database by getting the initial database from a libp2p Rendezvous. The app can host a rendezvous, so it is possible to bootstrap nearby friends to groups over wifi, QR code or bluetooth LE.

The app has a settings panel where the user can manage groups they subscribe to. The user can see and modify their recommendation algorithm. The algorithm runs locally and prioritizes trust over tags.

The UI style is like Tinder, but has a late 90's punk aesthetic. It has an underground vibe, an OLED-black background. It doesn't look very fancy, but it doesn't look bad either. It looks cool, like grunge. The logo might look like the attached image. The UI is made with React Native.

## First "optimized" version

A web-based event discovery and distribution platform called "flyers" (flyers.lol) that allows users to create, share, and discover events through decentralized networks.

Core Features:
- Event Creation & Management: Create events with pictures/videos, date, description, tags, location (text + coordinates), sound, and action buttons (registration/booking)
- Distribution Networks: Join or create public/private event groups based on geographic areas or topics (e.g., "copenhagen", "poetry")
- Interactive Event Interface: Swipe-based interaction system (left: dislike, right: like, up: like + add to calendar, down: moderation tools)
- User Settings: Manage group subscriptions and customize recommendation algorithm preferences

Visual References:
Inspired by Tinder's swipe interface combined with a more punk Eventbrite's event presentation style, featuring modern social event discovery elements.

Style Guide:
- Colors: Primary #FF4B4B (vibrant red), Secondary #29B6F6 (bright blue), Accent #FF375F (neon pink), Neutral #F8F9FA (light grey), Text #212529 (dark grey), Success #00E676 (neon green)
- Design: SF Pro Text/Inter fonts, card-based swipeable interface, location input with neon red highlights, clean event details layout, minimalist group management interface


##
A web-based event discovery and distribution platform called "flyers" that enables users to share and discover events through decentralized networks.

Core Features:
- Event Creation & Discovery: Create and browse events with pictures/videos, dates, descriptions, tags, locations, and optional features (sound, action buttons)
- Swipe-based Interaction: Swipe interface for event interactions (left to dislike, right to like, up to add to calendar, down for moderation)
- Group Management: Create and join private distribution networks based on geographic areas or topics
- Settings & Recommendations: Manage subscribed groups and customize recommendation algorithms that prioritize trust over tags

Visual References:
Inspired by Tinder's swipe mechanics with a 90's punk/grunge aesthetic, featuring an OLED-black background and underground vibe.

Style Guide:
- Colors: Primary #000000 (OLED black), Secondary #FF3333 (neon red), Accent #00FF00 (punk green), Text #FFFFFF (white), UI Elements #333333 (dark grey)
- Typography: Fonts that evoke punk/grunge aesthetic while maintaining readability
- Layout: Card-based swipe interface, minimal UI elements, high contrast design
- Interactive Elements: Smooth swipe animations, clear visual feedback for actions

Note: While the original requirements specified a mobile app with IPFS and decentralized features, this web version maintains the core functionality and aesthetic while being compatible with Replit's constraints.
