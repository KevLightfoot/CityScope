import { setupSearch } from "./search.js";
import { setupMap } from "./map.js";
import { setupPanel } from "./panel.js";

const map = setupMap();

setupSearch(map);
setupPanel();