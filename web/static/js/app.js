import { setupSearch } from "./search.js?v=2";
import { setupMap } from "./map.js?v=2";
import { setupPanel } from "./panel.js?v=2";

const map = setupMap();

setupSearch();
setupPanel();